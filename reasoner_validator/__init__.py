from typing import Optional, List, Dict
from os.path import join, abspath, dirname
from reasoner_validator.report import ValidationReporter
from reasoner_validator.biolink import (
    check_biolink_model_compliance_of_query_graph,
    check_biolink_model_compliance_of_knowledge_graph,
    BiolinkValidator
)

# Maximum number of data points to scrutinize
# in various parts TRAPI Query Response.Message
from reasoner_validator.trapi import check_trapi_validity, TRAPISchemaValidator
from reasoner_validator.trapi.mapping import MappingValidator, check_node_edge_mappings

TEST_DATA_SAMPLE_SIZE = 10


class TRAPIResponseValidator(ValidationReporter):
    """
    TRAPI Validator is an overall wrapper class for validating
    conformance of TRAPI Responses to TRAPI and the Biolink Model.
    """

    def __init__(
            self,
            trapi_version: Optional[str] = None,
            biolink_version: Optional[str] = None,
            sources: Optional[Dict] = None,
            strict_validation: bool = False
    ):
        """
        :param trapi_version: version of component against which to validate the message (mandatory, no default)
        :type trapi_version: str
        :param biolink_version: Biolink Model (SemVer) release against which the knowledge graph is to be
                                validated (Default: if None, use the Biolink Model Toolkit default version).
        :type biolink_version: Optional[str] = None
        :param sources: Dictionary of validation context identifying the ARA and KP for provenance attribute validation
        :type sources: Dict
        :param strict_validation: if True, some tests validate as 'error'; None or False, simply issue a 'warning'
        :type strict_validation: Optional[bool] = None
        """
        ValidationReporter.__init__(
            self,
            prefix="Validate TRAPI Response",
            trapi_version=trapi_version,
            biolink_version=biolink_version,
            sources=sources,
            strict_validation=strict_validation
        )

    def check_compliance_of_trapi_response(self, message: Dict):
        """
        One stop validation of all components of a TRAPI-schema compliant
        Query Response.Message against a designated Biolink Model release.
        Here, a TRAPI Response message is a Python Dictionary with three entries:

        * Query Graph ("QGraph"): knowledge graph query input parameters
        * Knowledge Graph: output knowledge (sub-)graph containing knowledge (Biolink Model compliant nodes, edges)
                           returned from the target resource (KP, ARA) for the query.
        * Results: a list of (annotated) node and edge bindings pointing into the Knowledge Graph, to represent the
                   specific answers (subgraphs) satisfying the query graph constraints.

        :param message: Response.Message to be validated.
        :type message: Dict

        :returns: Validator cataloging "information", "warning" and "error" messages (may be empty)
        :rtype: ValidationReporter
        """
        if not message:
            self.report("error.trapi.response.message.empty")
        # Sequentially validate the Query Graph, Knowledge Graph then validate
        # the Results (which rely on the validity of the other two components)
        elif self.has_valid_query_graph(message) and \
                self.has_valid_knowledge_graph(message):
            self.has_valid_results(message)

    @staticmethod
    def sample_results(results: List) -> List:
        """

        :param results: List, original list of Results
        :return: List, TEST_DATA_SAMPLE_SIZE sized subset of Results
        """
        sample_size = min(TEST_DATA_SAMPLE_SIZE, len(results))
        result_subsample = results[0:sample_size]
        return result_subsample

    @staticmethod
    def sample_graph(graph: Dict) -> Dict:
        """

        :param graph: Dict, original knowledge graph
        :return: Dict, TEST_DATA_SAMPLE_SIZE sized subset of knowledge graph
        """
        kg_sample: Dict = {
            "nodes": dict(),
            "edges": dict()
        }
        sample_size = min(TEST_DATA_SAMPLE_SIZE, len(graph["edges"]))
        n = 0
        for key, edge in graph['edges'].items():
            kg_sample['edges'][key] = edge
            if 'subject' in edge and edge['subject'] in graph['nodes']:
                kg_sample['nodes'][edge['subject']] = graph['nodes'][edge['subject']]
            if 'object' in edge and edge['object'] in graph['nodes']:
                kg_sample['nodes'][edge['object']] = graph['nodes'][edge['object']]
            n += 1
            if n > sample_size:
                break

        return kg_sample

    def has_valid_query_graph(self, message: Dict) -> bool:
        """
        Validate a TRAPI Query Graph.
        :param message: input message expected to contain the 'query_graph'
        :return: bool, False, if validation errors
        """
        # Query Graph must not be missing...
        if 'query_graph' not in message:
            self.report(code="error.trapi.response.query_graph.missing")
        else:
            # ... nor empty
            query_graph = message['query_graph']
            if not (query_graph and len(query_graph) > 0):
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

                # Validate the Biolink Model compliance of the Query Graph
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

    def has_valid_knowledge_graph(self, message: Dict) -> bool:
        """
        Validate a TRAPI Knowledge Graph.
        :param message: input message expected to contain the 'knowledge_graph'
        :return: bool, False, if validation errors
        """
        # The Knowledge Graph should not be missing
        if 'knowledge_graph' not in message:
            self.report(code="error.trapi.response.knowledge_graph.missing")
        else:
            knowledge_graph = message['knowledge_graph']
            # The Knowledge Graph should also not generally be empty? Issue a warning
            if not (
                    knowledge_graph and len(knowledge_graph) > 0 and
                    "nodes" in knowledge_graph and len(knowledge_graph["nodes"]) > 0 and
                    "edges" in knowledge_graph and len(knowledge_graph["edges"]) > 0
            ):
                self.report(code="warning.response.knowledge_graph.empty")
                # An empty knowledge graph (warning) does not generally invalidate
                # the whole Message, but no more validation tests are needed
            else:
                mapping_validator: MappingValidator = check_node_edge_mappings(knowledge_graph)
                if mapping_validator.has_messages():
                    self.merge(mapping_validator)

                # ...then if not empty, validate a subgraph sample of the associated
                # Knowledge Graph (since some TRAPI response kg's may be huge!)
                kg_sample = self.sample_graph(knowledge_graph)

                # Verify that the sample of the knowledge graph is TRAPI compliant
                trapi_validator: TRAPISchemaValidator = check_trapi_validity(
                    instance=kg_sample,
                    component="KnowledgeGraph",
                    trapi_version=self.trapi_version
                )
                if trapi_validator.has_messages():
                    self.merge(trapi_validator)

                # Verify that the sample of the knowledge graph is
                # compliant to the currently applicable Biolink Model release
                biolink_validator: BiolinkValidator = check_biolink_model_compliance_of_knowledge_graph(
                    graph=kg_sample,
                    biolink_version=self.biolink_version,
                    sources=self.sources,
                    # the ValidationReporter calling this function *might*
                    # have an explicit strict_validation override (if not None)
                    strict_validation=self.strict_validation
                )
                if biolink_validator.has_messages():
                    self.merge(biolink_validator)

        # Only 'error' but not 'info' nor 'warning' messages invalidate the overall Message
        return False if self.has_errors() else True

    def has_valid_results(self, message: Dict) -> bool:
        """
        Validate a TRAPI Results.
        :param message: input message expected to contain the 'results'
        :return: bool, False, if validation errors
        """

        #     :param output_element: test target, as edge 'subject' or 'object'
        #     :type output_element: str
        #     :param output_node_binding: node 'a' or 'b' of the ('one hop') QGraph test query
        #     :type output_node_binding: str

        # The Message.Results key should not be missing?
        if 'results' not in message:
            self.report(code="error.trapi.response.results.missing")
        else:
            results = message['results']
            if not (results and len(results) > 0):
                self.report(code="warning.response.results.empty")
                # An empty result (warning) does not generally invalidate
                # the whole Message, but no more validation tests are needed
            elif not isinstance(results, List):
                # The Message.results should be an array of Result objects
                self.report(code="error.trapi.response.results.non_array")
            else:
                # Validate a subsample of a non-empty Message.results component.
                results_sample = self.sample_results(results)
                for result in results_sample:
                    trapi_validator: TRAPISchemaValidator = check_trapi_validity(
                        instance=result,
                        component="Result",
                        trapi_version=self.trapi_version
                    )
                    if trapi_validator.has_messages():
                        # Record the error messages associated with the Result set then... don't continue
                        self.merge(trapi_validator)

                    # TODO: here, we might wish to compare the Results against the contents of the KnowledgeGraph,
                    #       with respect to node input values from the QueryGraph but this is tricky to do solely
                    #       with the subsamples, which may not completely overlap.

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
                    #             input_id=case[output_element],
                    #             output_node_binding=output_node_binding
                    #         )
                    #         # data_dump=f"Resolved aliases:\n{','.join(output_aliases)}\n" +
                    #         #           f"Result object IDs:\n{_output(object_ids,flat=True)}"

        # Only 'error' but not 'info' nor 'warning' messages invalidate the overall Message
        return False if self.has_errors() else True
