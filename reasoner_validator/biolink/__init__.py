"""
Version-specific Biolink Model semantic validation of knowledge graph components.
"""
from typing import Optional, Any, Dict, List, Tuple, Set
from enum import Enum
from functools import lru_cache
from urllib.error import HTTPError
from pprint import PrettyPrinter
import re
import logging

from bmt import Toolkit
from linkml_runtime.linkml_model import ClassDefinition

from reasoner_validator.util import SemVer, SemVerError

logger = logging.getLogger(__name__)

pp = PrettyPrinter(indent=4)

# TODO: is there a better way to ensure that a Biolink Model compliance test
#       runs quickly enough if the knowledge graph is very large?
#       Limiting nodes and edges viewed may miss deeply embedded errors(?)
_MAX_TEST_NODES = 1000
_MAX_TEST_EDGES = 100


def _get_biolink_model_schema(biolink_version: Optional[str] = None) -> Optional[str]:
    # Get Biolink Model Schema
    if biolink_version:
        try:
            svm = SemVer.from_string(biolink_version, ignore_prefix='v')

            # Sanity check: override SemVer object to ignore prerelease and
            # buildmetadata variants of the Biolink Version given
            svm = SemVer(major=svm.major, minor=svm.minor, patch=svm.patch)
        except SemVerError:
            raise TypeError(
                "The 'biolink_version' argument '"
                + biolink_version
                + "' is not a properly formatted semantic version?"
            )

        if svm >= SemVer.from_string("2.2.14"):
            biolink_version = "v" + str(svm)
        else:
            biolink_version = str(svm)
        schema = f"https://raw.githubusercontent.com/biolink/biolink-model/{biolink_version}/biolink-model.yaml"
        return schema
    else:
        return None


# At any given time, only a modest number of Biolink Model versions
# are expected to be active targets for SRI Test validations?
@lru_cache(maxsize=3)
def get_biolink_model_toolkit(biolink_version: Optional[str] = None) -> Toolkit:
    """
    Return Biolink Model Toolkit corresponding to specified version of the model (Default: current 'latest' version).

    :param biolink_version: Optional[str], caller specified Biolink Model version (default: None)
    :type biolink_version: Optional[str] or None
    :return: Biolink Model Toolkit.
    :rtype: Toolkit

    """
    if biolink_version:
        # If errors occur while instantiating non-default Toolkit;
        # then log the error but just use default as a workaround?
        try:
            biolink_schema = _get_biolink_model_schema(biolink_version=biolink_version)
            bmtk = Toolkit(biolink_schema)
            return bmtk
        except (TypeError, HTTPError) as ex:
            logger.error(str(ex))

    # 'latest' default Biolink Model
    # version of given Toolkit returned
    return Toolkit()


class TrapiGraphType(Enum):
    """ Enum type of Biolink Model compliant graph data being validated."""
    Edge_Object = "Input Edge"
    Query_Graph = "Query Graph"
    Knowledge_Graph = "Knowledge Graph"


class BiolinkValidator:
    """
    Wrapper class for Biolink Model validation.
    """
    def __init__(self, graph_type: TrapiGraphType, biolink_version: Optional[str] = None):
        """
        BiolinkValidator constructor.

        :param graph_type: type of graph data being validated
        :type graph_type: TrapiGraphType
        :param biolink_version: caller specified Biolink Model version (default: None)
        :type biolink_version: Optional[str] or None
        """
        self.graph_type = graph_type
        self.bmtk = get_biolink_model_toolkit(biolink_version=biolink_version)
        self.errors: Set[str] = set()
        self.nodes: Set[str] = set()

    def report_error(self, err_msg: str):
        """
        Capture an annotated error message to report from the BiolinkValidator.

        :param err_msg: error message to report.
        :type err_msg: str
        """
        self.errors.add(f"BLM Version {self.get_biolink_model_version()} Error in {self.graph_type.value}: {err_msg}")

    def get_biolink_model_version(self) -> str:
        """
        :return: Biolink Model version currently targeted by the validator.
        :rtype biolink_version: str
        """
        return self.bmtk.get_model_version()

    def minimum_required_biolink_version(self, version: str) -> bool:
        """

        :param version: simple 'major.minor.patch' Biolink Model SemVer
        :return: True if current version is equal to, or newer than, a targeted 'minimum_version'
        """
        try:
            current: SemVer = SemVer.from_string(self.bmtk.get_model_version())
            target: SemVer = SemVer.from_string(version)
            return current >= target
        except SemVerError as sve:
            logger.error(f"minimum_required_biolink_version() error: {str(sve)}")
            return False

    @staticmethod
    def is_curie(s: str) -> bool:
        """
        Check if a given string is a CURIE.

        :param s: str, string to be validated as a CURIE
        :return: bool, whether or not the given string is a CURIE
        """
        # Method copied from kgx.prefix_manager.PrefixManager...
        if isinstance(s, str):
            m = re.match(r"^[^ <()>:]*:[^/ :]+$", s)
            return bool(m)
        else:
            return False

    def get_reference(self, curie: str) -> Optional[str]:
        """
        Get the object_id reference of a given CURIE.

        Parameters
        ----------
        curie: str
            The CURIE

        Returns
        -------
        Optional[str]
            The reference of a CURIE

        """
        # Method adapted from kgx.prefix_manager.PrefixManager...
        reference: Optional[str] = None
        if self.is_curie(curie):
            reference = curie.split(":", 1)[1]
        return reference

    def get_result(self) -> Tuple[str, Optional[List[str]]]:
        """
        Get result of validation.
        :return: model version of the validation and list of detected errors.
        :rtype Tuple[str, Optional[List[str]]]
        """
        return self.bmtk.get_model_version(), list(self.errors)

    def validate_graph_node(self, node_id, slots: Dict[str, Any]):
        """
        Validate slot properties (mainly 'categories') of a node.

        :param node_id: identifier of a concept node
        :type node_id: str
        :param slots: properties of the node
        :type slots: Dict
        """
        logger.debug(f"{node_id}: {str(slots)}")

        if self.graph_type is TrapiGraphType.Knowledge_Graph:
            # TODO: this will fail for an earlier TRAPI data schema version
            #       which didn't use the tag 'categories' for nodes...
            #       probably no longer relevant to the community?
            if 'categories' in slots:
                if not isinstance(slots["categories"], List):
                    self.report_error(f"The value of node '{node_id}.categories' should be an array?")
                else:
                    categories = slots["categories"]
                    node_prefix_mapped: bool = False
                    for category in categories:
                        category: Optional[ClassDefinition] = \
                            self.validate_category(context="Node", category=category, strict_validation=False)
                        if category:
                            possible_subject_categories = self.bmtk.get_element_by_prefix(node_id)
                            if category.name in possible_subject_categories:
                                node_prefix_mapped = True
                    if not node_prefix_mapped:
                        self.report_error(
                            f"For all node categories [{','.join(categories)}] of " +
                            f"'{node_id}', the CURIE prefix namespace remains unmapped?"
                        )
            else:
                self.report_error(f"Node '{node_id}' is missing its 'categories'?")
            # TODO: Do we need to (or can we) validate other Knowledge Graph node fields here? Perhaps yet?

        else:  # Query Graph node validation

            if "ids" in slots:
                ids = slots["ids"]
                if not isinstance(ids, List):
                    self.report_error(f"Node '{node_id}.ids' slot value is not an array?")
                elif not ids:
                    self.report_error(f"Node '{node_id}.ids' slot array is empty?")
            else:
                ids: List[str] = list()  # null "ids" value is permitted in QNodes

            if "categories" in slots:
                categories = slots["categories"]
                if not isinstance(categories, List):
                    self.report_error(f"Node '{node_id}.categories' slot value is not an array?")
                elif not categories:
                    self.report_error(f"Node '{node_id}.categories' slot array is empty?")
                else:
                    id_prefix_mapped: Dict = {identifier: False for identifier in ids}
                    for category in categories:
                        # category validation may report an error internally
                        category: Optional[ClassDefinition] = \
                            self.validate_category(context="Node", category=category, strict_validation=False)
                        if category:
                            for identifier in ids:  # may be empty list if not provided...
                                possible_subject_categories = self.bmtk.get_element_by_prefix(identifier)
                                if category.name in possible_subject_categories:
                                    id_prefix_mapped[identifier] = True
                    unmapped_ids = [
                        identifier for identifier in id_prefix_mapped.keys() if not id_prefix_mapped[identifier]
                    ]
                    if unmapped_ids:
                        self.report_error(
                            f"Node '{node_id}.ids' have {str(unmapped_ids)} " +
                            f"that are unmapped to any of the Biolink Model categories {str(categories)}?")

            # else:  # null "categories" value is permitted in QNodes

            if 'is_set' in slots:
                is_set = slots["is_set"]
                if not isinstance(is_set, bool):
                    self.report_error(f"Node '{node_id}.is_set' slot is not a boolean value?")
            # else:  # a null "is_set" value is permitted in QNodes but defaults to 'False'

            # constraints  # TODO: how do we validate node constraints?
            pass

    def set_nodes(self, nodes: Set):
        self.nodes.update(nodes)

    def validate_graph_edge(self, edge: Dict):
        """
        Validate slot properties of a relationship ('biolink:Association') edge.

        :param edge: dictionary of slot properties of the edge.
        :type edge: dict[str, str]
        """
        # logger.debug(edge)

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
        attributes: List = edge['attributes'] if 'attributes' in edge else None

        edge_id = f"{str(subject_id)}--{edge_label}->{str(object_id)}"

        if not subject_id:
            self.report_error(f"Edge '{edge_id}' has a missing or empty 'subject' slot value?")
        elif subject_id not in self.nodes:
            self.report_error(
                f"Edge 'subject' id '{subject_id}' is missing from the nodes catalog?"
            )

        if self.graph_type is TrapiGraphType.Knowledge_Graph:
            if not predicate:
                self.report_error(f"Edge '{edge_id}' has a missing or empty predicate slot?")
            elif not self.bmtk.is_predicate(predicate):
                self.report_error(f"'{predicate}' is an unknown Biolink Model predicate?")
            elif self.minimum_required_biolink_version("2.2.0") and \
                    not self.bmtk.is_translator_canonical_predicate(predicate):
                self.report_error(f"predicate '{predicate}' is non-canonical?")
        else:  # is a Query Graph...
            if predicates is None:
                # Query Graphs can have a missing or null predicates slot
                pass
            elif not isinstance(predicates, List):
                self.report_error(f"Edge '{edge_id}' predicate slot value is not an array?")
            elif len(predicates) is 0:
                self.report_error(f"Edge '{edge_id}' predicate slot value is an empty array?")
            else:
                # Should now be a non-empty list of CURIES which are valid Biolink Predicates
                for predicate in predicates:
                    if not self.bmtk.is_predicate(predicate):
                        self.report_error(f"'{predicate}' is an unknown Biolink Model predicate?")
                    elif self.minimum_required_biolink_version("2.2.0") and \
                            not self.bmtk.is_translator_canonical_predicate(predicate):
                        self.report_error(f"predicate '{predicate}' is non-canonical?")
        if not object_id:
            self.report_error(f"Edge '{edge_id}' has a missing or empty 'object' slot value?")
        elif object_id not in self.nodes:
            self.report_error(f"Edge 'object' id '{object_id}' is missing from the nodes catalog?")

        if self.graph_type is TrapiGraphType.Knowledge_Graph:
            if not attributes:
                # For now, we simply assume that *all* edges must have *some* attributes
                # (at least, provenance related, but we don't explicitly test for them)
                self.report_error(f"Edge '{edge_id}' has missing or empty attributes?")
            else:
                # TODO: attempt some deeper attribute validation here
                for attribute in attributes:
                    attribute_type_id: Optional[str] = attribute.get('attribute_type_id', None)
                    if not attribute_type_id:
                        self.report_error(
                            f"Edge '{edge_id}' attribute '{str(attribute)}' missing its 'attribute_type_id'?"
                        )
                        continue
                    value: Optional[str] = attribute.get('value', None)
                    if not value:
                        self.report_error(
                            f"Edge '{edge_id}' attribute '{str(attribute)}' missing its 'value'?"
                        )
                        continue
                    #
                    # TODO: not sure if this should only be a Pytest 'warning' rather than an Pytest 'error'
                    #
                    if not self.is_curie(attribute_type_id):
                        self.report_error(
                            f"Edge '{edge_id}' attribute_type_id '{str(attribute_type_id)}' is not a CURIE?"
                        )
                    elif not self.bmtk.is_association_slot(attribute_type_id):
                        self.report_error(
                            f"Edge '{edge_id}' attribute_type_id '{str(attribute_type_id)}' " +
                            "not a biolink:association_slot?"
                        )
                        # if not a Biolink association_slot, at least, check if it is known to Biolink
                        prefix = attribute_type_id.split(":", 1)[0]
                        if not (prefix == 'biolink' or self.bmtk.get_element_by_prefix(prefix)):
                            self.report_error(
                                f"Edge '{edge_id}' attribute_type_id '{str(attribute_type_id)}' " +
                                f"has a CURIE prefix namespace unknown to Biolink?"
                            )
        else:
            # TODO: do we need to validate Query Graph 'constraints' slot contents here?
            pass

    def validate_category(
            self,
            context: str,
            category: Optional[str],
            strict_validation: bool = True
    ) -> ClassDefinition:
        """

        :param context: str, label for context of concept whose category is being validated, i.e. 'Subject' or 'Object'
        :param category: str, CURIE of putative concept 'category'
        :param strict_validation: bool, True report mixin or abstract categories as errors; Ignore otherwise if False
        :return:
        """
        biolink_class: Optional[ClassDefinition] = None
        if category:
            biolink_class = self.bmtk.get_element(category)
            if biolink_class:
                if biolink_class.deprecated:
                    self.report_error(
                        f"{context} Biolink class '{category}' is deprecated: {biolink_class.deprecated}?"
                    )
                    biolink_class = None
                elif biolink_class.abstract:
                    if strict_validation:
                        self.report_error(
                            f"{context} Biolink class '{category}' is abstract, not a concrete category?"
                        )
                    else:
                        logger.info(f"{context} Biolink class '{category}' is abstract. Ignored in this context.")
                    biolink_class = None
                elif self.bmtk.is_mixin(category):
                    # A mixin cannot be instantiated so it should not be given as an input concept category
                    if strict_validation:
                        self.report_error(
                            f"{context} identifier '{category}' designates a mixin, not a concrete category?"
                        )
                    else:
                        logger.info(f"{context} Biolink class '{category}' is a 'mixin'. Ignored in this context.")
                    biolink_class = None
                elif not self.bmtk.is_category(category):
                    self.report_error(f"{context} identifier '{category}' is not a valid Biolink category?")
                    biolink_class = None
            else:
                self.report_error(f"{context} Biolink class '{category}' is unknown?")
        else:
            self.report_error(f"{context} category identifier is missing?")

        return biolink_class

    def validate_input_node(self, context: str, category: Optional[str], identifier: Optional[str]):

        biolink_class: Optional[ClassDefinition] = self.validate_category(f"Input {context}", category)

        if identifier:
            if biolink_class:
                possible_subject_categories = self.bmtk.get_element_by_prefix(identifier)
                if biolink_class.name not in possible_subject_categories:
                    err_msg = f"Namespace prefix of input {context} identifier '{identifier}' is unmapped to '{category}'?"
                    self.report_error(err_msg)
            # else, we will have already reported an error in validate_category()
        else:
            self.report_error(f"Input {context} identifier is missing?")

    def check_biolink_model_compliance_of_input_edge(self, edge: Dict[str, str]) -> Tuple[str, Optional[List[str]]]:
        """
        Validate a templated test input edge contents against the current BMT Biolink Model release.

        Sample method 'edge' with expected dictionary tags:

        {
            'subject_category': 'biolink:AnatomicalEntity',
            'object_category': 'biolink:AnatomicalEntity',
            'predicate': 'biolink:subclass_of',
            'subject': 'UBERON:0005453',
            'object': 'UBERON:0035769'
        }

        :param edge: basic dictionary of a templated input edge - S-P-O including concept Biolink Model categories
        :type edge: Dict[str,str]
        :return: Biolink Model version (str) and List[str] (possibly empty) of error messages
        :rtype: Tuple[str, List[str]]
        """
        # data fields to be validated...
        subject_category_curie = edge['subject_category'] if 'subject_category' in edge else None
        object_category_curie = edge['object_category'] if 'object_category' in edge else None
        predicate_curie = edge['predicate'] if 'predicate' in edge else None
        subject_curie = edge['subject'] if 'subject' in edge else None
        object_curie = edge['object'] if 'object' in edge else None

        self.validate_input_node(
            context='subject',
            category=subject_category_curie,
            identifier=subject_curie
        )

        if not (predicate_curie and self.bmtk.is_predicate(predicate_curie)):
            err_msg = f"Input predicate "
            err_msg += f"'{predicate_curie}' is unknown?" if predicate_curie else "is missing?"
            self.report_error(err_msg)
        elif self.minimum_required_biolink_version("2.2.0") and \
                not self.bmtk.is_translator_canonical_predicate(predicate_curie):
            self.report_error(f"Input predicate '{predicate_curie}' is non-canonical?")

        self.validate_input_node(
            context='object',
            category=object_category_curie,
            identifier=object_curie
        )

        return self.get_result()

    def check_biolink_model_compliance(self, graph: Dict) -> Tuple[str, Optional[List[str]]]:
        """
        Validate a TRAPI-schema compliant Message graph-like data structure
        against the currently active Biolink Model Toolkit model version.
    
        :param graph: knowledge graph to be validated
        :type graph: Dict
        :returns: 2-tuple of Biolink Model version (str) and List[str] (possibly empty) of error messages
        :rtype: Tuple[str, Optional[List[str]]]
        """
        if not graph:
            self.report_error(f"Empty graph?")

        # Access graph data fields to be validated
        nodes: Optional[Dict]
        if 'nodes' in graph and graph['nodes']:
            nodes = graph['nodes']
        else:
            # Query Graphs can have an empty nodes catalog
            if self.graph_type is not TrapiGraphType.Query_Graph:
                self.report_error(f"No nodes found?")
            # else:  Query Graphs can omit the 'nodes' tag
            nodes = None

        edges: Optional[Dict]
        if 'edges' in graph and graph['edges']:
            edges = graph['edges']
        else:
            if self.graph_type is not TrapiGraphType.Query_Graph:
                self.report_error(f"No edges found?")
            # else:  Query Graphs can omit the 'edges' tag
            edges = None

        # I only do a sampling of node and edge content. This ensures that
        # the tests are performant but may miss errors deeper inside the graph?
        nodes_seen = 0
        if nodes:
            for node_id, details in nodes.items():

                self.validate_graph_node(node_id, details)

                nodes_seen += 1
                if nodes_seen >= _MAX_TEST_NODES:
                    break

            # Needed for the subsequent edge validation
            self.set_nodes(set(nodes.keys()))

            edges_seen = 0
            if edges:
                for edge in edges.values():

                    # print(f"{str(edge)}", flush=True)
                    self.validate_graph_edge(edge)

                    edges_seen += 1
                    if edges_seen >= _MAX_TEST_EDGES:
                        break

        return self.get_result()


def check_biolink_model_compliance_of_input_edge(
        edge: Dict[str, str],
        biolink_version: Optional[str] = None
) -> Tuple[str, Optional[List[str]]]:
    """
    Validate an input edge object contents against the current BMT Biolink Model release.

    Sample method 'edge' with expected dictionary tags:

    {
        'subject_category': 'biolink:AnatomicalEntity',
        'object_category': 'biolink:AnatomicalEntity',
        'predicate': 'biolink:subclass_of',
        'subject': 'UBERON:0005453',
        'object': 'UBERON:0035769'
    }

    :param edge: basic contents of a templated input edge - S-P-O including concept Biolink Model categories
    :type edge: Dict[str,str]
    :param biolink_version: Biolink Model (SemVer) version against which the edge object is to be validated
    :type biolink_version: Optional[str] = None
    :returns: 2-tuple of Biolink Model version (str) and List[str] (possibly empty) of error messages
    :rtype: Tuple[str, Optional[List[str]]]
    """
    validator = BiolinkValidator(graph_type=TrapiGraphType.Edge_Object, biolink_version=biolink_version)
    return validator.check_biolink_model_compliance_of_input_edge(edge)


def check_biolink_model_compliance_of_query_graph(
        graph: Dict,
        biolink_version: Optional[str] = None
) -> Tuple[str, Optional[List[str]]]:
    """
    Validate a TRAPI-schema compliant Message Query Graph against the current BMT Biolink Model release.

    Since a Query graph is usually an incomplete knowledge graph specification,
    the validation undertaken is not 'strict'

    :param graph: query graph to be validated
    :type graph: Dict
    :param biolink_version: Biolink Model (SemVer) version against which the query graph is to be validated
    :type biolink_version: Optional[str] = None
    :return: 2-tuple of Biolink Model version (str) and List[str] (possibly empty) of error messages
    :rtype: Tuple[str, Optional[List[str]]]
    """
    validator = BiolinkValidator(graph_type=TrapiGraphType.Query_Graph, biolink_version=biolink_version)
    return validator.check_biolink_model_compliance(graph)


def check_biolink_model_compliance_of_knowledge_graph(
        graph: Dict,
        biolink_version: Optional[str] = None
) -> Tuple[str, Optional[List[str]]]:
    """
    Strict validation of a TRAPI-schema compliant Message Knowledge Graph against the active BMT Biolink Model release.

    :param graph: knowledge graph to be validated.
    :type graph: Dict
    :param biolink_version: Biolink Model (SemVer) version against which the knowledge graph is to be validated
    :type biolink_version: Optional[str] = None
    :return: 2-tuple of Biolink Model version (str) and List[str] (possibly empty) of error messages
    :rtype: Tuple[str, Optional[List[str]]]
    """
    validator = BiolinkValidator(graph_type=TrapiGraphType.Knowledge_Graph, biolink_version=biolink_version)
    return validator.check_biolink_model_compliance(graph)
