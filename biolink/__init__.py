"""
Biolink Compliance testing support

Ideally, this code should probably reside outside the reasoner-validator project
(in fact, we are shameless copying it over from the SRI Testing translator.biolink package for now)
but until the shared project package publication issues are sorted out, we duplicate it here.

TODO: copied from https://github.com/TranslatorSRI/SRI_testing/blob/main/translator/biolink/__init__.py
      on April 27, 2022 (check for updates or package publication to pypi?)
"""
from typing import Optional, Dict, List, Tuple, Set
from enum import Enum
from functools import lru_cache
from pprint import PrettyPrinter
import re
import logging

from bmt import Toolkit

logger = logging.getLogger(__name__)

pp = PrettyPrinter(indent=4)

# TODO: review and fix issue that a Biolink Model compliance test
#       could run too slowly, if the knowledge graph is very large?
_MAX_TEST_NODES = 1
_MAX_TEST_EDGES = 1

# Biolink Release number should be a well-formed Semantic Version
semver_pattern = re.compile(r"^\d+\.\d+\.\d+$")


def get_biolink_model_schema(biolink_release: Optional[str] = None) -> Optional[str]:
    """
    Get Biolink Model Schema
    """
    if biolink_release:
        if not semver_pattern.fullmatch(biolink_release):
            raise TypeError(
                "The 'biolink_release' argument '"
                + biolink_release
                + "' is not a properly formatted 'major.minor.patch' semantic version?"
            )
        schema = f"https://raw.githubusercontent.com/biolink/biolink-model/{biolink_release}/biolink-model.yaml"
        return schema
    else:
        return None


_bmt_toolkit: Optional[Toolkit] = None


# At any given time, only a modest number of Biolink Model versions
# are expected to be active targets for SRI Test validations?
@lru_cache(maxsize=10)
def set_biolink_model_toolkit(biolink_version=None) -> str:
    # Note here that we let BMT control which version of Biolink we are using,
    # unless the value for which is overridden on the CLI
    global _bmt_toolkit

    # Toolkit takes a couple of seconds to initialize, so don't want it initialized per-test; however,
    # TODO: if we eventually need per-test settings, maybe we should cache various versions locally
    #       (see https://github.com/biolink/kgx/blob/master/kgx/utils/kgx_utils.py#L304).
    if biolink_version:
        biolink_schema = get_biolink_model_schema(biolink_release=biolink_version)
        _bmt_toolkit = Toolkit(biolink_schema)
    else:
        _bmt_toolkit = Toolkit()

    return _bmt_toolkit.get_model_version()


def get_toolkit() -> Optional[Toolkit]:
    global _bmt_toolkit
    if not _bmt_toolkit:
        raise RuntimeError("Biolink Model Toolkit is not initialized?!?")
    return _bmt_toolkit


class TrapiGraphType(Enum):
    Query_Graph = "Query"
    Knowledge_Graph = "Knowledge"


class BiolinkValidator:

    def __init__(self, graph_type: TrapiGraphType):
        """
        :param graph_type: type of graph data being validated
        """
        self.graph_type = graph_type
        self.error_prefix = f"{self.graph_type.value} Graph Error: "
        self.bmtk: Toolkit = get_toolkit()
        self.errors: Set[str] = set()
        self.nodes: Set[str] = set()

    def report_error(self, err_msg):
        self.errors.add(err_msg)

    def get_result(self) -> Tuple[str, Optional[List[str]]]:
        return self.bmtk.get_model_version(), list(self.errors)

    def validate_category(self, node_id: str, category: str) -> Optional[str]:
        if self.bmtk.is_category(category):
            return self.bmtk.get_element(category).name
        elif self.bmtk.is_mixin(category):
            # finding mixins in the categories is OK, but we otherwise ignore them in validation
            logger.info(f"\nReported Biolink Model category '{category}' resolves to a Biolink Model 'mixin'?")
        else:
            element = self.bmtk.get_element(category)
            if element:
                # got something here... hopefully just an abstract class
                # but not a regular category, so we also ignore it!
                # TODO: how do we better detect abstract classes from the model?
                #       How strict should our validation be here?
                logger.info(
                    f"\nReported Biolink Model category '{category}' " +
                    "resolves to the (possibly abstract) " +
                    f"Biolink Model element '{element.name}'?")
            else:
                # Error: a truly unrecognized category?
                self.errors.add(
                    f"{self.error_prefix}'{category}' for node '{node_id}' " +
                    "is not a recognized Biolink Model category?"
                )
        return None

    def validate_node(self, node_id, details):

        logger.debug(f"{node_id}: {str(details)}")

        if self.graph_type is TrapiGraphType.Knowledge_Graph:
            # TODO: this will fail for an earlier TRAPI data schema version
            #       which didn't use the tag 'categories' for nodes...
            #       probably no longer relevant to the community?
            if 'categories' in details:
                if not isinstance(details["categories"], List):
                    self.errors.add(f"{self.error_prefix}The value of node '{node_id}.categories' should be an array?")
                else:
                    categories = details["categories"]
                    node_prefix_mapped: bool = False
                    for category in categories:
                        category_name: str = self.validate_category(node_id, category)
                        if category_name:
                            possible_subject_categories = self.bmtk.get_element_by_prefix(node_id)
                            if category_name in possible_subject_categories:
                                node_prefix_mapped = True
                    if not node_prefix_mapped:
                        self.errors.add(
                            f"{self.error_prefix}For all node categories [{','.join(categories)}] of " +
                            f"'{node_id}', the CURIE prefix namespace remains unmapped?"
                        )
            else:
                self.errors.add(f"{self.error_prefix}Node '{node_id}' is missing its 'categories'?")
            # TODO: Do we need to (or can we) validate other Knowledge Graph node fields here? Perhaps yet?

        else:  # Query Graph node validation
            # ids
            if "ids" in details:
                ids = details["ids"]
                if not isinstance(ids, List):
                    self.errors.add(f"{self.error_prefix}Node '{node_id}.ids' slot value is not an array?")
                elif not ids:
                    self.errors.add(f"{self.error_prefix}Node '{node_id}.ids' slot array is empty?")
                else:
                    for id in ids:
                        # TODO: maybe somehow check if the ids are valid CURIES in a Biolink registered namespace?
                        pass
            # else:  # null "ids" value is permitted in QNodes

            if "categories" in details:
                categories = details["categories"]
                if not isinstance(categories, List):
                    self.errors.add(f"{self.error_prefix}Node '{node_id}.categories' slot value is not an array?")
                elif not categories:
                    self.errors.add(f"{self.error_prefix}Node '{node_id}.categories' slot array is empty?")
                else:
                    for category in categories:
                        category_name: str = self.validate_category(node_id, category)
                        if not category_name:
                            self.errors.add(
                                f"{self.error_prefix}Node '{node_id} category '{category}' "
                                "is unknown in the current Biolink Model?"
                            )
            # else:  # null "categories" value is permitted in QNodes

            if 'is_set' in details:
                is_set = details["is_set"]
                if not isinstance(is_set, bool):
                    self.errors.add(f"{self.error_prefix}Node '{node_id}.is_set' slot is not a boolean value?")
            # else:  # a null "is_set" value is permitted in QNodes but defaults to 'False'

            # constraints  # TODO: how do we validate node constraints?
            pass

    def set_nodes(self, nodes: Set):
        self.nodes.update(nodes)

    def validate_edge(self, edge: Dict):

        logger.debug(edge)

        # edge data fields to be validated...
        subject_id = edge['subject'] if 'subject' in edge else None

        predicates = predicate = None
        if self.graph_type is TrapiGraphType.Knowledge_Graph:
            predicate = edge['predicate'] if 'predicate' in edge else None
            edge_label = predicate
        else:
            # Query Graph...
            predicates = edge['predicates'] if 'predicates' in edge else None
            edge_label = str(predicates)

        object_id = edge['object'] if 'object' in edge else None
        attributes = edge['attributes'] if 'attributes' in edge else None

        edge_id = f"{str(subject_id)}--{edge_label}->{str(object_id)}"

        if not subject_id:
            self.errors.add(f"{self.error_prefix}Edge '{edge_id}' has a missing or empty 'subject' slot value?")
        elif subject_id not in self.nodes:
            self.errors.add(
                f"{self.error_prefix}Edge subject id '{subject_id}' is missing from the nodes catalog?"
            )

        if self.graph_type is TrapiGraphType.Knowledge_Graph:
            if not predicate:
                self.errors.add(f"{self.error_prefix}Edge '{edge_id}' has a missing or empty predicate slot?")
        else:  # is a Query Graph...
            if predicates is None:
                # Query Graphs can have a null predicates value
                pass
            elif not isinstance(predicates, List):
                self.errors.add(f"{self.error_prefix}Edge '{edge_id}' predicate slot value is not an array?")
            else:
                # Should be a non-empty list of CURIES which are valid Biolink Predicates
                for predicate in predicates:
                    if not self.bmtk.is_predicate(predicate):
                        self.errors.add(f"{self.error_prefix}'{predicate}' is an unknown Biolink Model predicate?")

        if not object_id:
            self.errors.add(f"{self.error_prefix}Edge '{edge_id}' has a missing or empty 'object' slot value?")
        elif object_id not in self.nodes:
            self.errors.add(f"{self.error_prefix}Edge object id '{object_id}' is missing from the nodes catalog?")

        if self.graph_type is TrapiGraphType.Knowledge_Graph:
            if not attributes:
                # TODO: not quite sure whether and how to fully validate the 'attributes' of an edge
                # For now, we simply assume that *all* edges must have *some* attributes
                # (at least, provenance related, but we don't explicitly test for them)
                self.errors.add(f"{self.error_prefix}Edge '{edge_id}' has missing or empty attributes?")
        else:
            # TODO: validate Query Graph constraints here?
            pass

    def check_biolink_model_compliance(self, graph: Dict) -> Tuple[str, Optional[List[str]]]:
        """
        Validate a TRAPI-schema compliant Message graph-like data structure
        against the currently active BMT Biolink Model release.
    
        :param graph: knowledge graph to be validated
        :param graph_type: type of graph data being validated, either 'Query' or 'Knowledge'
    
        The 'strict' parameter is set to False if only a Query Graph or similar partial graph fragment is being validated.
    
        :returns: 2-tuple of Biolink Model version (str) and List[str] (possibly empty) of error messages
        """
        # Access knowledge graph data fields to be validated... fail early if missing...
        nodes: Optional[Dict]
        if 'nodes' in graph and graph['nodes']:
            nodes = graph['nodes']
        else:
            # Query Graphs can have an empty nodes catalog
            if self.graph_type is not TrapiGraphType.Query_Graph:
                self.report_error(f"TRAPI Error: No nodes found in the {self.graph_type.value} Graph?")
            nodes = None

        edges: Optional[Dict]
        if 'edges' in graph and graph['edges']:
            edges = graph['edges']
        else:
            # Query Graphs can have an empty edges catalog
            if self.graph_type is not TrapiGraphType.Query_Graph:
                self.report_error(f"TRAPI Error: No edges found in the {self.graph_type.value} Graph?")
            edges = None

        # I only do a sampling of node and edge content. This ensures that
        # the tests are performant but may miss errors deeper inside the graph?
        nodes_seen = 0
        if nodes:
            for node_id, details in nodes.items():

                self.validate_node(node_id, details)

                nodes_seen += 1
                if nodes_seen >= _MAX_TEST_NODES:
                    break

            # Needed for the subsequent edge validation
            self.set_nodes(set(nodes.keys()))

            edges_seen = 0
            if edges:
                for edge in edges.values():

                    # print(f"{str(edge)}", flush=True)
                    self.validate_edge(edge)

                    edges_seen += 1
                    if edges_seen >= _MAX_TEST_EDGES:
                        break

        return self.get_result()


# TODO: need to add some additional Biolink Model validation of the query graph data
def check_biolink_model_compliance_of_query_graph(graph: Dict) -> Tuple[str, Optional[List[str]]]:
    """
    Validate a TRAPI-schema compliant Message Query Graph against the current BMT Biolink Model release.

    Since a Query graph is usually an incomplete knowledge graph specification,
    the validation undertaken is not 'strict'

    :param graph: knowledge graph to be validated

    :returns: 2-tuple of Biolink Model version (str) and List[str] (possibly empty) of error messages
    """
    validator = BiolinkValidator(graph_type=TrapiGraphType.Query_Graph)
    return validator.check_biolink_model_compliance(graph)


def check_biolink_model_compliance_of_knowledge_graph(graph: Dict) -> Tuple[str, Optional[List[str]]]:
    """
    Strict validation of a TRAPI-schema compliant Message Knowledge Graph against the active BMT Biolink Model release.

    :param graph: knowledge graph to be validated

    :returns: 2-tuple of Biolink Model version (str) and List[str] (possibly empty) of error messages
    """
    validator = BiolinkValidator(graph_type=TrapiGraphType.Knowledge_Graph)
    return validator.check_biolink_model_compliance(graph)
