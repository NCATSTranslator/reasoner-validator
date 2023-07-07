from typing import Optional, List, Dict

from bmt import Toolkit
from reasoner_validator.report import ValidationReporter
from reasoner_validator.biolink import (
    check_biolink_model_compliance_of_query_graph,
    check_biolink_model_compliance_of_knowledge_graph,
    BMTWrapper,
    BiolinkValidator,
    get_biolink_model_toolkit,
    TRAPIGraphType
)

# Maximum number of data points to scrutinize
# in various parts TRAPI Query Response.Message
from reasoner_validator.trapi import (
    TRAPI_1_3_0_SEMVER,
    TRAPI_1_4_0_SEMVER,
    TRAPI_1_4_1_SEMVER,
    TRAPI_1_4_0_BETA3_SEMVER,
    TRAPI_1_4_0_BETA4_SEMVER,
    LATEST_TRAPI_MAJOR_RELEASE_SEMVER,
    LATEST_TRAPI_RELEASE_SEMVER,
    LATEST_TRAPI_RELEASE,
    check_trapi_validity,
    TRAPISchemaValidator
)
from reasoner_validator.trapi.mapping import MappingValidator, check_node_edge_mappings
from reasoner_validator.versioning import SemVer, SemVerError
from reasoner_validator.sri.util import get_aliases

import logging
logger = logging.getLogger(__name__)

# Unspoken assumption here is that validation of results returned for
# Biolink Model release compliance only needs to be superficial
RESULT_TEST_DATA_SAMPLE_SIZE = 10


class TRAPIResponseValidator(ValidationReporter):
    """
    TRAPI Validator is an overall wrapper class for validating
    conformance of TRAPI Responses to TRAPI and the Biolink Model.
    """
    def __init__(
            self,
            trapi_version: Optional[str] = None,
            biolink_version: Optional[str] = None,
            strict_validation: bool = False,
            suppress_empty_data_warnings: bool = False
    ):
        """
        :param trapi_version: version of component against which to validate the message (mandatory, no default)
        :type trapi_version: str
        :param biolink_version: Biolink Model (SemVer) release against which the knowledge graph is to be
                                validated (Default: if None, use the Biolink Model Toolkit default version).
        :type biolink_version: Optional[str] = None
        :param strict_validation: if True, some tests validate as 'error'; None or False, simply issue a 'warning'
        :type strict_validation: Optional[bool] = None
        :param suppress_empty_data_warnings: validation normally reports empty Message query graph, knowledge graph
                       and results as warnings. This flag suppresses the reporting of such warnings (default: False).
        :type suppress_empty_data_warnings: bool
        """
        ValidationReporter.__init__(
            self,
            prefix="Validate TRAPI Response",
            trapi_version=trapi_version,
            biolink_version=biolink_version,
            strict_validation=strict_validation
        )
        self._is_trapi_1_4: Optional[bool] = None
        self.suppress_empty_data_warnings: bool = suppress_empty_data_warnings

    def is_trapi_1_4(self) -> bool:
        assert self.trapi_version
        try:  # try block ... Sanity check: in case the trapi_version is somehow invalid?
            target_major_version: SemVer = SemVer.from_string(self.trapi_version, core_fields=['major', 'minor'])
            self._is_trapi_1_4 = target_major_version >= LATEST_TRAPI_MAJOR_RELEASE_SEMVER
        except SemVerError as sve:
            logger.error(f"Current TRAPI release '{self.trapi_version}' seems invalid: {str(sve)}. Reset to latest?")
            self.trapi_version = LATEST_TRAPI_RELEASE
            self._is_trapi_1_4 = True
        return self._is_trapi_1_4

    def sanitize_trapi_response(self, response: Dict) -> Dict:
        """
        Some component TRAPI Responses cannot be validated further due to missing tags and None values.
        This method is a temporary workaround to sanitize the query for additional validation.

        :param response: Dict full TRAPI Response JSON object
        :return: Dict, response with discretionary removal of content which
                       triggers (temporarily) unwarranted TRAPI validation failures
        """
        # Temporary workaround for "1.4.0-beta4" schema bugs
        current_version: SemVer = SemVer.from_string(self.trapi_version)
        # the message is not empty
        if 'knowledge_graph' in response['message'] and response['message']['knowledge_graph'] is not None and \
                TRAPI_1_4_0_BETA4_SEMVER >= current_version != TRAPI_1_3_0_SEMVER:
            for key, edge in response['message']['knowledge_graph']['edges'].items():
                edge_id = f"{str(edge['subject'])}--{str(edge['predicate'])}->{str(str(edge['object']))}"
                if 'sources' not in edge or not edge['sources']:
                    self.report("error.knowledge_graph.edge.sources.missing", identifier=edge_id)
                    continue
                for source in edge['sources']:
                    if 'source_record_urls' not in source or source['source_record_urls'] is None:
                        source['source_record_urls'] = list()
                    if 'upstream_resource_ids' not in source or source['upstream_resource_ids'] is None:
                        source['upstream_resource_ids'] = list()

        # 'auxiliary_graphs' (introduced the TRAPI 1.4.0-beta3 pre-releases,
        # full fixed in the 1.4.1 release) ought to be nullable.
        if TRAPI_1_4_0_SEMVER >= current_version >= TRAPI_1_4_0_BETA3_SEMVER and \
                ('auxiliary_graphs' not in response['message'] or response['message']['auxiliary_graphs'] is None):
            response['message']['auxiliary_graphs'] = dict()

        if 'workflow' in response and response['workflow']:
            # a 'workflow' is a list of steps, which are JSON object specifications
            workflow_steps: List[Dict] = response['workflow']
            for step in workflow_steps:
                if 'runner_parameters' in step and not step['runner_parameters']:
                    self.report("warning.trapi.response.workflow.runner_parameters.null")
                    step.pop('runner_parameters')
                if 'parameters' in step and not step['parameters']:
                    # There are some workflow types that have mandatory need for 'parameters'
                    # but this should be caught in a later schema validation step
                    self.report("warning.trapi.response.workflow.parameters.null")
                    step.pop('parameters')
        return response

    def check_compliance_of_trapi_response(
            self,
            response: Optional[Dict],
            max_kg_edges: int = 0,
            max_results: int = 0,
            target_provenance: Optional[Dict] = None
    ):
        """
        One stop validation of all components of a TRAPI-schema compliant
        Query.Response, including its Message against a designated Biolink Model release.
        The high level structure of a Query.Response is described in
        https://github.com/NCATSTranslator/ReasonerAPI/blob/master/docs/reference.md#response-.

        The TRAPI Query.Response.Message is a Python Dictionary with three entries:

        * Query Graph ("QGraph"): knowledge graph query input parameters
        * Knowledge Graph: output knowledge (sub-)graph containing knowledge (Biolink Model compliant nodes, edges)
                           returned from the target resource (KP, ARA) for the query.
        * Results: a list of (annotated) node and edge bindings pointing into the Knowledge Graph, to represent the
                   specific answers (subgraphs) satisfying the query graph constraints.

        :param response: Query.Response to be validated.
        :type response: Optional[Dict]
        :param max_kg_edges: integer maximum number of edges to be validated from the
                                     knowledge graph of the response. A value of zero triggers validation
                                      of all edges in the knowledge graph (Default: 0 - use all edges)
        :type max_kg_edges: int
        :param max_results: target sample number of results to validate (default: 0 for 'use all results').
        :type max_results: int
        :param target_provenance: Dictionary of validation context identifying the ARA and KP for provenance attribute validation
        :type target_provenance: Dict

        :returns: Validator cataloging "information", "warning" and "error" messages (could be empty)
        :rtype: ValidationReporter
        """
        if not (response and "message" in response):
            if not self.suppress_empty_data_warnings:
                self.report("error.trapi.response.empty")

            # nothing more to validate?
            return

        message: Optional[Dict] = response['message']
        if not message:
            if not self.suppress_empty_data_warnings:
                self.report("error.trapi.response.message.empty")

            # ... also, nothing more here to validate?
            return

        response = self.sanitize_trapi_response(response)

        trapi_validator: TRAPISchemaValidator = check_trapi_validity(
            instance=response,
            component="Response",
            trapi_version=self.trapi_version
        )
        if trapi_validator.has_messages():
            self.merge(trapi_validator)

        status: Optional[str] = response['status'] if 'status' in response else None
        if status and status not in ["OK", "Success", "QueryNotTraversable", "KPsNotAvailable"]:
            self.report("warning.trapi.response.status.unknown", identifier=status)

        # Sequentially validate the Query Graph, Knowledge Graph then validate
        # the Results (which rely on the validity of the other two components)
        elif self.has_valid_query_graph(message) and \
                self.has_valid_knowledge_graph(message, max_kg_edges, target_provenance):
            self.has_valid_results(message, max_results)

    @staticmethod
    def sample_results(results: List, sample_size: int = 0) -> List:
        """
        Subsample the results to a maximum size of 'sample_size'

        :param results: List, original list of Results
        :param sample_size: int, target sample size (default: 0 for 'use all results').

        :return: List, 'sample_size' sized subset of Results
        """
        if sample_size > 0:
            sample_size = min(sample_size, len(results))
            return results[0:sample_size]
        else:
            return results

    @staticmethod
    def sample_graph(graph: Dict, edges_limit: int = 0) -> Dict:
        """
        Only process a strict subsample of the TRAPI Response Message knowledge graph.

        :param graph: original knowledge graph
        :type graph: Dict
        :param edges_limit: integer maximum number of edges to be validated in the knowledge graph. A value of zero
                            triggers validation of all edges in the knowledge graph (Default: 0 - use all edges)
        :type edges_limit: int

        :return: Dict, 'edges_limit' sized subset of knowledge graph
        """
        # We don't check for non-empty graphs here simply because the sole caller of this
        # method is the 'has_valid_knowledge_graph' method, which filters out empty graphs
        if edges_limit > 0:
            kg_sample: Dict = {
                "nodes": dict(),
                "edges": dict()
            }
            # 'sample_size' will always be a positive number here.
            # The kg_sample size will always be the 'sample_size'
            # or less, the latter situation arising if the number
            # of graph edges is smaller or some subject or
            # object ids are missing in the nodes list.
            sample_size = min(edges_limit, len(graph["edges"]))
            n = 0
            for key, edge in graph['edges'].items():

                kg_sample['edges'][key] = edge

                if 'subject' in edge and \
                        edge['subject'] in graph['nodes'] and \
                        edge['subject'] not in kg_sample['nodes']:
                    kg_sample['nodes'][edge['subject']] = graph['nodes'][edge['subject']]

                if 'object' in edge and \
                        edge['object'] in graph['nodes'] and \
                        edge['object'] not in kg_sample['nodes']:
                    kg_sample['nodes'][edge['object']] = graph['nodes'][edge['object']]

                n += 1
                if n == sample_size:
                    break

            return kg_sample

        else:
            # No pruning... just return the contents of the entire knowledge graph
            return {
                "nodes": graph["nodes"],
                "edges": graph["edges"]
            }

    def has_valid_query_graph(self, message: Dict) -> bool:
        """
        Validate a TRAPI Query Graph.
        :param message: input message expected to contain the 'query_graph'
        :return: bool, False, if validation errors
        """
        # Query Graph must not be missing...
        if 'query_graph' not in message:
            if not self.suppress_empty_data_warnings:
                self.report(code="error.trapi.response.query_graph.missing")
        else:
            # ... nor empty
            query_graph = message['query_graph']
            if not (query_graph and len(query_graph) > 0):
                if not self.suppress_empty_data_warnings:
                    self.report(code="error.trapi.response.query_graph.empty")
            else:
                # Validate the TRAPI compliance of the Query Graph
                trapi_validator: TRAPISchemaValidator = check_trapi_validity(
                    instance=query_graph,
                    component="QueryGraph",
                    trapi_version=self.trapi_version
                )
                if trapi_validator.has_messages():
                    self.merge(trapi_validator)

                if self.validate_biolink():
                    # Conduct validation of Biolink Model compliance
                    # of the Query Graph, if not suppressed...
                    biolink_validator = check_biolink_model_compliance_of_query_graph(
                        graph=query_graph,
                        biolink_version=self.biolink_version,
                        # the ValidationReporter calling this function *might*
                        # have an explicit strict_validation override (if not None)
                        strict_validation=self.strict_validation
                    )
                    if biolink_validator.has_messages():
                        self.merge(biolink_validator)
                        # 'info' and 'warning' messages do
                        # not fully invalidate the query_graph

        # Only 'error' but not 'info' nor 'warning' messages invalidate the overall Message
        return False if self.has_errors() else True

    def has_valid_knowledge_graph(
            self,
            message: Dict,
            edges_limit: int = 0,
            target_provenance: Optional[Dict] = None
    ) -> bool:
        """
        Validate a TRAPI Knowledge Graph.

        :param message: input message expected to contain the 'knowledge_graph'
        :type message: Dict
        :param edges_limit: integer maximum number of edges to be validated in the knowledge graph. A value of zero
                            triggers validation of all edges in the knowledge graph (Default: 0 - use all edges)
        :type edges_limit: int
        :param target_provenance: Dictionary of validation context identifying the ARA and KP for provenance attribute validation
        :type target_provenance: Dict

        :return: bool, False, if validation errors
        """
        # This integrity constraint may not really be necessary
        # since negative numbers are functionally equivalent to zero
        assert edges_limit >= 0, "The 'edges_limit' must be zero or a positive integer!"

        # The Knowledge Graph should not be missing
        if 'knowledge_graph' not in message:
            if not self.suppress_empty_data_warnings:
                self.report(code="error.trapi.response.knowledge_graph.missing")
        else:
            knowledge_graph = message['knowledge_graph']
            # The Knowledge Graph should also not generally be empty? Issue a warning
            if not (
                    knowledge_graph and len(knowledge_graph) > 0 and
                    "nodes" in knowledge_graph and knowledge_graph["nodes"] and
                    "edges" in knowledge_graph and knowledge_graph["edges"]
            ):
                # An empty knowledge graph (warning) does not generally invalidate
                # the whole Message, but no more validation tests are needed
                if not self.suppress_empty_data_warnings:
                    self.report(code="warning.trapi.response.knowledge_graph.empty")
            else:
                mapping_validator: MappingValidator = check_node_edge_mappings(knowledge_graph)
                if mapping_validator.has_messages():
                    self.merge(mapping_validator)

                # ...then if not empty, validate a subgraph sample of the associated
                # Knowledge Graph (since some TRAPI response kg's may be huge!)
                kg_sample = self.sample_graph(graph=knowledge_graph, edges_limit=edges_limit)

                # Verify that the sample of the knowledge graph is TRAPI compliant
                trapi_validator: TRAPISchemaValidator = check_trapi_validity(
                    instance=kg_sample,
                    component="KnowledgeGraph",
                    trapi_version=self.trapi_version
                )
                if trapi_validator.has_messages():
                    self.merge(trapi_validator)

                if self.validate_biolink():
                    # Conduct validation of Biolink Model compliance of the
                    # Knowledge Graph, if Biolink validation not suppressed...
                    biolink_validator: BiolinkValidator = \
                        check_biolink_model_compliance_of_knowledge_graph(
                            graph=kg_sample,
                            trapi_version=self.trapi_version,
                            biolink_version=self.biolink_version,
                            target_provenance=target_provenance,
                            # the ValidationReporter calling this function *might*
                            # have an explicit strict_validation override (if not None)
                            strict_validation=self.strict_validation
                        )
                    if biolink_validator.has_messages():
                        self.merge(biolink_validator)

        # Only 'error' but not 'info' nor 'warning' messages invalidate the overall Message
        return False if self.has_errors() else True

    def has_valid_results(self, message: Dict, sample_size: int = 0) -> bool:
        """
        Validate a TRAPI Results.

        :param message: input message expected to contain the 'results'
        :param sample_size: int, sample number of results to validate (default: 0 for 'use all results').

        :return: bool, False, if validation errors
        """

        #     :param output_element: test target, as edge 'subject' or 'object'
        #     :type output_element: str
        #     :param output_node_binding: node 'a' or 'b' of the ('one hop') QGraph test query
        #     :type output_node_binding: str

        # The Message.Results key should not be missing?
        if 'results' not in message:
            if not self.suppress_empty_data_warnings:
                self.report(code="error.trapi.response.results.missing")
        else:
            results = message['results']

            if not (results and len(results) > 0):
                if not self.suppress_empty_data_warnings:
                    self.report(code="warning.trapi.response.results.empty")
                    # An empty result (warning) does not generally invalidate
                    # the whole Message, but no more validation tests are needed

            elif not isinstance(results, List):
                # The Message.results should be an array of Result objects
                # TODO: Is this test unnecessary, since TRAPI schema
                #       validation (below) should normally catch this?
                self.report(code="error.trapi.response.results.non_array")

            else:
                # Validate a subsample of a non-empty Message.results component.
                results_sample = self.sample_results(results, sample_size=sample_size)
                for result in results_sample:

                    # generally validate against the pertinent schema
                    trapi_validator: TRAPISchemaValidator = check_trapi_validity(
                        instance=result,
                        component="Result",
                        trapi_version=self.trapi_version
                    )
                    if trapi_validator.has_messages():
                        # Record the error messages associated with the Result set then... don't continue
                        self.merge(trapi_validator)

                    # Maybe some additional TRAPI-release specific non-schematic validation here?
                    if self.is_trapi_1_4():
                        # TODO: implement me!
                        pass
                    else:
                        pass

                    # TODO: here, we could try to compare the Results against the contents of the KnowledgeGraph,
                    #       with respect to node input values from the QueryGraph, but this is tricky to do solely
                    #       with the subsamples, which may not completely overlap,
                    #       and may also be somewhat computationally intensive?

                    # ...Finally, check that the sample Results contained the object of the Query

                    # The 'output_element' is 'subject' or 'object' target (unknown) of retrieval
                    # The 'output_node_binding' is (subject) 'a' or (object) 'b' keys in
                    # the QueryGraph.Nodes to be bound
                    # In principle, we detect which node in the QueryGraph has 'ids' associated with its node record
                    # and assume that the other edge node is the desired target (in the OneHop), so the 'ids'
                    # there should be in the output

                    # object_ids = [r['node_bindings'][output_node_binding][0]['id'] for r in results_sample]
                    # if case[output_element] not in object_ids:
                    #     # The 'get_aliases' method uses the Translator NodeNormalizer to check if any of
                    #     # the aliases of the case[output_element] identifier are in the object_ids list
                    #     output_aliases = get_aliases(case[output_element])
                    #     if not any([alias == object_id for alias in output_aliases for object_id in object_ids]):
                    #         validator.report(
                    #             code=error.results.missing_bindings,
                    #             identifier=case[output_element],
                    #             output_node_binding=output_node_binding
                    #         )
                    #         # data_dump=f"Resolved aliases:\n{','.join(output_aliases)}\n" +
                    #         #           f"Result object IDs:\n{_output(object_ids,flat=True)}"

        # Only 'error' but not 'info' nor 'warning' messages invalidate the overall Message
        return False if self.has_errors() else True

    @staticmethod
    def case_node_found(target: str, identifiers: List[str], case: Dict, nodes: Dict) -> bool:
        """
        Check for presence of the target identifier,
        with expected categories, in the "nodes" catalog.

        :param target: 'subject' or 'object'
        :param identifiers: List of node (CURIE) identifiers to be checked in the "nodes" catalog
        :param case: Dict, full test case (to access the target node 'category')
        :param nodes: Dict, nodes category indexed by node identifiers.
        :return:
        """
        #
        #     "nodes": {
        #         "MONDO:0005148": {"name": "type-2 diabetes"},
        #         "CHEBI:6801": {"name": "metformin", "categories": ["biolink:Drug"]}
        #     }
        #

        # Sanity check
        assert target in ["subject", "object"]
        for identifier in identifiers:
            if identifier in nodes.keys():
                # Found the target node identifier,
                # but is the expected category present?
                node_details = nodes[identifier]
                if "categories" in node_details:
                    category = case[f"{target}_category"]
                    if category in node_details["categories"]:
                        return True

        # Target node identifier or categories is missing,
        # or not annotated with the expected category?
        return False

    @staticmethod
    def case_edge_bindings(target_edge_id: str, data: Dict) -> bool:
        """
        Check if target query edge id and knowledge graph edge id are in specified edge_bindings.
        :param target_edge_id:  str, expected knowledge edge identifier in a matching result
        :param data: TRAPI version-specific Response context from which the 'edge_bindings' may be retrieved
        :return: True, if found
        """
        edge_bindings: Dict = data["edge_bindings"]
        for bound_query_id, edge in edge_bindings.items():
            # The expected query identifier in this context is
            # hard coded as 'ab' in the 'one_hop.util.py' model
            if bound_query_id == "ab":
                for binding_details in edge:
                    # TRAPI schema validation actually
                    # catches missing id's, but sanity check...
                    if "id" in binding_details:
                        if target_edge_id == binding_details["id"]:
                            return True
        return False

    def case_result_found(
            self,
            subject_id: str,
            object_id: str,
            edge_id: str,
            results: List,
            trapi_version: str
    ) -> bool:
        """
        Validate that test case S--P->O edge is found bound to the Results?
        :param subject_id: str, subject node (CURIE) identifier
        :param object_id:  str, subject node (CURIE) identifier
        :param edge_id:  str, subject node (CURIE) identifier
        :param results: List of (TRAPI-version specific) Result objects
        :param trapi_version: str, target TRAPI version of the Response being validated
        :return: bool, True if case S-P-O edge was found in the results
        """
        result_found: bool = False
        result: Dict

        for result in results:

            # Node binding validation still currently same for recent TRAPI versions
            node_bindings: Dict = result["node_bindings"]
            subject_id_found: bool = False
            object_id_found: bool = False
            edge_id_found: bool = False
            for node in node_bindings.values():
                for details in node:
                    if "id" in details:
                        if subject_id == details["id"]:
                            subject_id_found = True
                        if object_id == details["id"]:
                            object_id_found = True

            # However, TRAPI 1.4.0 Message 'Results' 'edge_bindings' are reported differently
            #          from 1.3.0, rather, embedded in 'Analysis' objects (and 'Auxiliary Graphs')
            if self.is_trapi_1_4():
                #
                #     "auxiliary_graphs": {
                #         "a0": {
                #             "edges": [
                #                 "e02",
                #                 "e12"
                #             ]
                #         },
                #         "a1": {
                #             "edges": [
                #                 "extra_edge0"
                #             ]
                #         },
                #         "a2": {
                #             "edges" [
                #                 "extra_edge1"
                #             ]
                #         }
                #     },
                #     "results": [
                #         {
                #             "node_bindings": {
                #                 "n0": [
                #                     "id": "diabetes"
                #                 ],
                #                 "n1": [
                #                     "id": "metformin"
                #                 ]
                #             },
                #             "analyses":[
                #                 {
                #                     "reasoner_id": "ara0",
                #                     "edge_bindings": {
                #                         "e0": [
                #                             {
                #                                 "id": "e01"
                #                             },
                #                             {
                #                                 "id": "creative_edge"
                #                             }
                #                         ]
                #                     },
                #                     "support_graphs": [
                #                         "a1",
                #                         "a2"
                #                     ]
                #                     "score": ".7"
                #                 },
                #             ]
                #         }
                #     ]

                # result["analyses"] may be empty but prior TRAPI 1.4.0 schema validation ensures that
                # the "analysis" key is at least present plus the objects themselves are 'well-formed'
                analyses: List = result["analyses"]
                for analysis in analyses:
                    edge_id_found = self.case_edge_bindings(edge_id, analysis)
                    if edge_id_found:
                        break

            else:
                # TRAPI 1.3.0 or earlier?
                #
                # Then, the TRAPI 1.3.0 Message Results (referencing the
                # Response Knowledge Graph) could be something like this:
                #
                #     "results": [
                #         {
                #             "node_bindings": {
                #                # node "id"'s in knowledge graph, in edge "id"
                #                 "type-2 diabetes": [{"id": "MONDO:0005148"}],
                #                 "drug": [{"id": "CHEBI:6801"}]
                #             },
                #             "edge_bindings": {
                #                 # the edge binding key should be the query edge id
                #                 # bounded edge "id" is from knowledge graph
                #                 "treats": [{"id": "df87ff82"}]
                #             }
                #         }
                #     ]
                #
                edge_id_found = self.case_edge_bindings(edge_id, result)

            if subject_id_found and object_id_found and edge_id_found:
                result_found = True
                break

        return result_found

    def case_input_found_in_response(
            self,
            case: Dict,
            response: Dict,
            trapi_version: str
    ) -> bool:
        """
        Predicate to validate if test data test case specified edge is returned
        in the Knowledge Graph of the TRAPI Response Message. This method assumes
        that the TRAPI response is already generally validated as well-formed.

        :param case: Dict, input data test case
        :param response: Dict, TRAPI Response whose message ought to contain the test case edge
        :param trapi_version: str, TRAPI version of response being tested
        :return: True if test case edge found; False otherwise
        """
        # sanity checks
        assert case, "case_input_found_in_response(): Empty or missing test case data!"
        assert response, "case_input_found_in_response(): Empty or missing TRAPI Response!"
        assert "message" in response, "case_input_found_in_response(): TRAPI Response missing its Message component!"
        assert trapi_version

        #
        # case: Dict parameter contains something like:
        #
        #     idx: 0,
        #     subject_category: 'biolink:SmallMolecule',
        #     object_category: 'biolink:Disease',
        #     predicate: 'biolink:treats',
        #     subject_id: 'CHEBI:3002',  # may have the deprecated key 'subject' here
        #     object_id: 'MESH:D001249', # may have the deprecated key 'object' here
        #
        # the contents for which ought to be returned in
        # the TRAPI Knowledge Graph, as a Result mapping?
        #

        message: Dict = response["message"]
        if not (
            "knowledge_graph" in message and message["knowledge_graph"] and
            "results" in message and message["results"]
        ):
            # empty knowledge graph is syntactically ok, but in
            # this, input test data edge is automatically deemed missing
            return False

        # TODO: We need to check **here*** whether or not the
        #       TRAPI response returned the original test case edge!!?!!
        #       Not totally sure if we should first search the Results then
        #       the Knowledge Graph, or go directly to the Knowledge Graph...

        # The Message Query Graph could be something like:
        # "query_graph": {
        #     "nodes": {
        #         "type-2 diabetes": {"ids": ["MONDO:0005148"]},
        #         "drug": {"categories": ["biolink:Drug"]}
        #     },
        #     "edges": {
        #         "treats": {
        #             "subject": "drug",
        #             "predicates": ["biolink:treats"],
        #             "object": "type-2 diabetes"
        #         }
        #     }
        # }
        #
        # with a Response Message Knowledge Graph
        # dictionary with 'nodes' and 'edges':
        #
        # "knowledge_graph": {
        #     "nodes": ...,
        #     "edges": ...
        # }
        knowledge_graph: Dict = message["knowledge_graph"]

        # In the Knowledge Graph:
        #
        #     "nodes": {
        #         "MONDO:0005148": {"name": "type-2 diabetes"},
        #         "CHEBI:6801": {"name": "metformin", "categories": ["biolink:Drug"]}
        #     }
        #
        # Check for case 'subject_id' and 'object_id',
        # with expected categories, in nodes catalog
        nodes: Dict = knowledge_graph["nodes"]
        subject_id = case["subject_id"] if "subject_id" in case else case["subject"]
        subject_aliases = get_aliases(subject_id)
        if not self.case_node_found("subject", subject_aliases, case, nodes):
            # 'subject' node identifier not found?
            return False

        object_id = case["object_id"] if "object_id" in case else case["object"]
        object_aliases = get_aliases(object_id)
        if not self.case_node_found("object", object_aliases, case, nodes):
            # 'object' node identifier not found?
            return False

        # In the Knowledge Graph:
        #
        #     "edges": {
        #         "df87ff82": {
        #             "subject": "CHEBI:6801",
        #             "predicate": "biolink:treats",
        #             "object": "MONDO:0005148"
        #         }
        #     }
        #
        # Check in the edges catalog for an edge containing
        # the case 'subject_id', 'predicate' and 'object_id'
        edges: Dict = knowledge_graph["edges"]

        bmtw = BMTWrapper(biolink_version=self.biolink_version)

        predicate = case["predicate"]

        bmt: Optional[Toolkit] = bmtw.get_bmt()
        predicate_descendants: List[str]
        inverse_predicate_descendants: List[str] = list()  # may sometimes remain empty...
        if bmt is not None:
            predicate_descendants = bmt.get_descendants(predicate, formatted=True)
            inverse_predicate = bmtw.get_inverse_predicate(predicate)
            if inverse_predicate:
                inverse_predicate_descendants = bmt.get_descendants(inverse_predicate, formatted=True)
        else:
            # simpler case in which we are ignoring deep Biolink Model validation
            predicate_descendants = [predicate]

        edge_id_match: Optional[str] = None
        subject_match: Optional[str] = None
        object_match: Optional[str] = None
        for edge_id, edge in edges.items():
            # Note: this edge search could be arduous on a big knowledge graph?
            if edge["subject"] in subject_aliases and \
                    edge["predicate"] in predicate_descendants and \
                    edge["object"] in object_aliases:
                edge_id_match = edge_id
                subject_match = edge["subject"]
                object_match = edge["object"]
                break
            elif edge["subject"] in object_aliases and \
                    edge["predicate"] in inverse_predicate_descendants and \
                    edge["object"] in subject_aliases:
                # observation of the inverse edge is also counted as a match?
                subject_match = edge["subject"]
                object_match = edge["object"]
                edge_id_match = edge_id
                break

        if edge_id_match is None:
            # Test case S--P->O edge not found?
            return False

        results: List = message["results"]
        if not self.case_result_found(subject_match, object_match, edge_id_match, results, trapi_version):
            # Some components of test case S--P->O edge
            # NOT bound within any Results?
            return False

        # By this point, the case data assumed to be
        # successfully validated in the TRAPI Response?
        return True
