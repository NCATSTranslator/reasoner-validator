"""
Version-specific Biolink Model semantic validation of knowledge graph components.
"""
from typing import Optional, Any, Dict, List, Tuple, Set
from enum import Enum
from functools import lru_cache
from urllib.error import HTTPError
from pprint import PrettyPrinter
import logging

from bmt import Toolkit
from linkml_runtime.linkml_model import ClassDefinition, Element

from reasoner_validator import is_curie
from reasoner_validator.report import ValidationReporter
from reasoner_validator.trapi import TRAPIValidator, check_trapi_validity, check_node_edge_mappings
from reasoner_validator.versioning import SemVer, SemVerError

logger = logging.getLogger(__name__)

pp = PrettyPrinter(indent=4)

# TODO: is there a better way to ensure that a Biolink Model compliance test
#       runs quickly enough if the knowledge graph is very large?
#       Limiting nodes and edges viewed may miss deeply embedded errors(?)
_MAX_TEST_NODES = 1000
_MAX_TEST_EDGES = 100

# Maximum number of data points to scrutinize
# in various parts TRAPI Query Response.Message
TEST_DATA_SAMPLE_SIZE = 10


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
            bmt = Toolkit(biolink_schema)
            return bmt
        except (TypeError, HTTPError) as ex:
            logger.error(str(ex))

    # 'latest' default Biolink Model
    # version of given Toolkit returned
    return Toolkit()


class TRAPIGraphType(Enum):
    """ Enum type of Biolink Model compliant graph data being validated."""
    Edge_Object = "Input Edge"
    Query_Graph = "Query Graph"
    Knowledge_Graph = "Knowledge Graph"


class BiolinkValidator(ValidationReporter):
    """
    Wrapper class for Biolink Model validation.
    """
    def __init__(self, graph_type: TRAPIGraphType, biolink_version: Optional[str] = None):
        """
        Biolink Validator constructor.

        :param graph_type: type of graph data being validated
        :type graph_type: TRAPIGraphType

        :param biolink_version: caller specified Biolink Model version (default: None)
        :type biolink_version: Optional[str] or None
        """
        self.bmt: Toolkit = get_biolink_model_toolkit(biolink_version=biolink_version)
        resolved_biolink_version = self.bmt.get_model_version()
        ValidationReporter.__init__(
            self,
            prefix=f"Biolink Validation of {graph_type.value}",
            biolink_version=resolved_biolink_version
        )
        self.graph_type: TRAPIGraphType = graph_type
        self.nodes: Set[str] = set()

    def minimum_required_biolink_version(self, version: str) -> bool:
        """
        :param version: simple 'major.minor.patch' Biolink Model SemVer
        :return: True if current version is equal to, or newer than, a targeted 'minimum_version'
        """
        try:
            current: SemVer = SemVer.from_string(self.biolink_version)
            target: SemVer = SemVer.from_string(version)
            return current >= target
        except SemVerError as sve:
            logger.error(f"minimum_required_biolink_version() error: {str(sve)}")
            return False

    def get_result(self) -> Tuple[str, Optional[Dict[str, List[Dict]]]]:
        """
        Get result of validation.

        :return: model version of the validation and dictionary of reported validation messages.
        :rtype Tuple[str, Optional[Dict[str, Set[str]]]]
        """
        return self.bmt.get_model_version(), self.get_messages()

    def validate_graph_node(self, node_id: str, slots: Dict[str, Any]):
        """
        Validate slot properties (mainly 'categories') of a node.

        :param node_id: identifier of a concept node
        :type node_id: str, node identifier
        :param slots: properties of the node
        :type slots: Dict
        """
        logger.debug(f"{node_id}: {str(slots)}")

        if self.graph_type is TRAPIGraphType.Knowledge_Graph:
            # TODO: this will fail for an earlier TRAPI data schema version
            #       which didn't use the tag 'categories' for nodes...
            #       probably no longer relevant to the community?
            if 'categories' in slots:
                if not isinstance(slots["categories"], List):
                    self.report(code="error.node.categories_not_array", node_id=node_id)
                else:
                    categories = slots["categories"]
                    node_prefix_mapped: bool = False
                    for category in categories:
                        category: Optional[ClassDefinition] = \
                            self.validate_category(
                                context="Knowledge Graph Node",
                                node_id=node_id,
                                category=category,
                                # Knowledge Graph Node categories
                                # cannot be 'abstract' or 'mixin'
                                strict_validation=True
                            )
                        if category:
                            possible_subject_categories = self.bmt.get_element_by_prefix(node_id)
                            if category.name in possible_subject_categories:
                                node_prefix_mapped = True
                    if not node_prefix_mapped:
                        self.report(code="warning.node.unmapped_prefix", node_id=node_id, categories=str(categories))
            else:
                self.report(code="error.node.category.missing", context=self.graph_type, node_id=node_id)

            # TODO: Do we need to (or can we) validate here, any other Knowledge Graph node fields? Perhaps not yet?

        else:  # Query Graph node validation

            if "ids" in slots and slots["ids"]:
                ids = slots["ids"]
                if not isinstance(ids, List):
                    self.report(code="error.node.ids_not_array", node_id=node_id)
                elif not ids:
                    self.report(code="error.node.empty_ids", node_id=node_id)
            else:
                ids: List[str] = list()  # null "ids" value is permitted in QNodes

            if "categories" in slots:
                categories = slots["categories"]
                if not isinstance(categories, List):
                    self.report(code="error.node.categories_not_array", node_id=node_id)
                elif not categories:
                    self.report(code="error.node.empty_categories", node_id=node_id)
                else:
                    id_prefix_mapped: Dict = {identifier: False for identifier in ids}
                    for category in categories:
                        # category validation may report an error internally
                        category: Optional[ClassDefinition] = \
                            self.validate_category(
                                context="Query Graph Node",
                                node_id=node_id,
                                category=category,
                                # Knowledge Graph Node categories are
                                # permitted to be 'abstract' or 'mixin'
                                strict_validation=False
                            )
                        if category:
                            for identifier in ids:  # may be empty list if not provided...
                                possible_subject_categories = self.bmt.get_element_by_prefix(identifier)
                                if category.name in possible_subject_categories:
                                    id_prefix_mapped[identifier] = True
                    unmapped_ids = [
                        identifier for identifier in id_prefix_mapped.keys() if not id_prefix_mapped[identifier]
                    ]
                    if unmapped_ids:
                        self.report(
                            code="warning.node.identifiers_unmapped_to_categories",
                            node_id=node_id,
                            unmapped_ids=str(unmapped_ids),
                            categories=str(categories)
                        )

            # else:  # null "categories" value is permitted in QNodes

            if 'is_set' in slots:
                is_set = slots["is_set"]
                if not isinstance(is_set, bool):
                    self.report(code="error.node.is_set_not_boolean", node_id=node_id)
            # else:  # a null "is_set" value is permitted in QNodes but defaults to 'False'

            # constraints  # TODO: how do we validate node constraints?
            pass

    def set_nodes(self, nodes: Set):
        self.nodes.update(nodes)

    def validate_element_status(self, context: str, name: str, strict_validation: bool) -> Optional[Element]:
        """
        Detect element missing from Biolink, or is deprecated, abstract or mixin, signalled as a failure or warning.

        :param context: parsing context (e.g. 'Node')
        :param name: name of putative Biolink element ('class')
        :param strict_validation: if True, abstract and mixin elements validate as 'error'; False, issue a 'warning'

        :return: Optional[Element], Biolink Element resolved to 'name' if element passed all validation; None otherwise.
        """
        element: Optional[Element] = self.bmt.get_element(name)
        if not element:
            self.report(code="error.unknown", context=context, name=name)
        elif element.deprecated:
            self.report(code="warning.deprecated", context=context, name=name)
            return None
        elif element.abstract:
            if strict_validation:
                self.report(code="error.abstract", context=context, name=name)
            else:
                self.report(code="info.abstract", context=context, name=name)
            return None
        elif self.bmt.is_mixin(name):
            # A mixin cannot be instantiated thus it should not be given as an input concept category
            if strict_validation:
                self.report(code="error.mixin", context=context, name=name)
            else:
                self.report(code="info.mixin", context=context, name=name)
            return None
        else:
            return element

    def validate_attributes(self, edge: Dict, context: Optional[Dict] = None):
        """
        :param edge: Dict, the edge object associated wich some attributes are expected to be found
        :param context: Dict, (optional) ARA or KP context of the edge
        :return: None (validation messages captured in the 'self' BiolinkValidator context)
        """
        if 'attributes' not in edge.keys():
            self.report(code="error.edge.attribute.missing")
        elif not edge['attributes']:
            self.report(code="error.edge.attribute.empty")
        elif not isinstance(edge['attributes'], List):
            self.report(code="error.edge.attribute.not_list")
        else:
            attributes = edge['attributes']

            ara_source: Optional[str] = None
            kp_source: Optional[str] = None
            kp_source_type: Optional[str] = None
            if context:
                ara_source = f"infores:{context['ara_source']}" \
                    if 'ara_source' in context and context['ara_source'] else ""
                kp_source = f"infores:{context['kp_source']}" \
                    if 'kp_source' in context and context['kp_source'] else ""
                kp_source_type = context['kp_source_type'] \
                    if 'kp_source_type' in context and context['kp_source_type'] else 'aggregator'
                kp_source_type = f"biolink:{kp_source_type}_knowledge_source"

            # Expecting ARA and KP 'aggregator_knowledge_source' attributes?
            found_ara_knowledge_source = False
            found_kp_knowledge_source = False
            found_primary_or_original_knowledge_source = False

            for attribute in attributes:

                # Validate attribute_type_id
                if 'attribute_type_id' not in attribute:
                    self.report(code="error.edge.attribute.type_id.missing")
                elif not attribute['attribute_type_id']:
                    self.report(code="error.edge.attribute.type_id.empty")
                elif 'value' not in attribute:
                    self.report(code="error.edge.attribute.value.missing")
                elif not attribute['value']:
                    self.report(code="error.edge.attribute.value.empty")
                else:
                    attribute_type_id: str = attribute['attribute_type_id']
                    value = attribute['value']

                    # TODO: there seems to be non-uniformity in provenance attribute values for some KP/ARA's
                    #       in which a value is returned as a Python list (of at least one element?) instead
                    #       of a string. Here, to ensure full coverage of the attribute values returned,
                    #       we'll coerce scalar values into a list, then iterate.
                    if not isinstance(value, List):
                        if isinstance(value, str):
                            value = [value]
                        else:
                            self.report(code="error.edge.attribute.value.invalid_data_type", data_type=type(value))
                            continue

                    if not is_curie(attribute_type_id):
                        self.report(
                            code="error.edge.attribute.type_id.not_curie",
                            attribute_type_id=str(attribute_type_id)
                        )
                    else:
                        # 'attribute_type_id' is a CURIE, but how well does it map?
                        prefix = attribute_type_id.split(":", 1)[0]
                        if prefix == 'biolink':
                            biolink_class = self.validate_element_status(
                                context="Attribute Type ID",
                                name=attribute_type_id,
                                strict_validation=True
                            )
                            if biolink_class:
                                if not self.bmt.is_association_slot(attribute_type_id):
                                    self.report(
                                        code="warning.edge.attribute.type_id.not_association_slot",
                                        attribute_type_id=str(attribute_type_id)
                                    )

                                else:
                                    # it is a Biolink 'association_slot' but now, validate what kind?

                                    # TODO: only check knowledge_source provenance here for now.
                                    #       Are there other association_slots to be validated here too?

                                    # Check Edge Provenance attributes
                                    if attribute_type_id not in \
                                            [
                                                "biolink:aggregator_knowledge_source",
                                                "biolink:primary_knowledge_source",
                                                "biolink:original_knowledge_source"

                                            ]:

                                        # TODO: not interested in any other attribute_type_id's at this moment
                                        continue

                                    if attribute_type_id in \
                                            [
                                                "biolink:primary_knowledge_source",
                                                "biolink:original_knowledge_source"
                                            ]:
                                        found_primary_or_original_knowledge_source = True

                                    # TODO: 'biolink:original_knowledge_source' KS is deprecated from Biolink 2.4.5
                                    if self.minimum_required_biolink_version("2.4.5") and \
                                       attribute_type_id == "biolink:original_knowledge_source":
                                        self.report(code="warning.provenance.deprecated")

                                    # ... now, check the infores values against various expectations
                                    for infores in value:
                                        if not infores.startswith("infores:"):
                                            self.report(code="error.provenance.not_an_infores", infores=infores)
                                        else:
                                            if ara_source and \
                                                    attribute_type_id == "biolink:aggregator_knowledge_source" and \
                                                    infores == ara_source:
                                                found_ara_knowledge_source = True
                                            elif kp_source and \
                                                    attribute_type_id == kp_source_type and \
                                                    infores == kp_source:
                                                found_kp_knowledge_source = True

                        # if not a Biolink association_slot, at least,
                        # check if it is an id prefix known to Biolink.
                        # We won't call it a hard error, but issue a warning
                        elif not self.bmt.get_element_by_prefix(prefix):
                            self.report(
                                code="warning.edge.attribute.type_id.unknown_prefix",
                                attribute_type_id=str(attribute_type_id)
                            )

                        else:
                            self.report(
                                code="info.attribute.type_id.non_biolink_prefix",
                                attribute_type_id=str(attribute_type_id)
                            )

            # TODO: After all the attributes have been scanned, check for provenance. Treat as warnings for now
            if ara_source and not found_ara_knowledge_source:
                self.report(code="warning.provenance.ara.missing")

            if kp_source and not found_kp_knowledge_source:
                self.report(
                    code="warning.edge.provenance.kp.missing",
                    kp_source=kp_source,
                    kp_source_type=kp_source_type
                )

            if not found_primary_or_original_knowledge_source:
                self.report(code="warning.provenance.missing_primary")

    def validate_predicate(self, predicate: str, strict_validation: bool):
        """
        :param predicate: putative Biolink Model predicate to be validated
        :param strict_validation: if True, abstract and mixin elements validate as 'error'; False, issue 'info' message.
        :type strict_validation: bool = False
        :return:
        """
        # Validate the putative predicate as *not* being abstract, deprecated or a mixin
        biolink_class = self.validate_element_status(
            context="Predicate",
            name=predicate,
            strict_validation=strict_validation
        )
        if biolink_class:
            if not self.bmt.is_predicate(predicate):
                self.report(code="error.predicate.unknown", predicate=predicate)
            elif self.minimum_required_biolink_version("2.2.0") and \
                    not self.bmt.is_translator_canonical_predicate(predicate):
                self.report(code="warning.edge.predicate.non_canonical", predicate=predicate)

    def validate_graph_edge(self, edge: Dict, strict_validation: bool):
        """
        Validate slot properties of a relationship ('biolink:Association') edge.

        :param edge: dictionary of slot properties of the edge.
        :type edge: dict[str, str]
        :param strict_validation: if True, abstract and mixin elements validate as 'error'; False, issue 'info' message.
        :type strict_validation: bool
        """
        # logger.debug(edge)
        # edge data fields to be validated...
        subject_id = edge['subject'] if 'subject' in edge else None

        predicates = predicate = None
        if self.graph_type is TRAPIGraphType.Knowledge_Graph:
            predicate = edge['predicate'] if 'predicate' in edge else None
            edge_label = predicate
        else:
            # Query Graph...
            predicates = edge['predicates'] if 'predicates' in edge else None
            edge_label = str(predicates)

        object_id = edge['object'] if 'object' in edge else None

        edge_id = f"{str(subject_id)}--{edge_label}->{str(object_id)}"

        if not subject_id:
            self.report(code="error.edge.subject.missing", edge_id=edge_id)
        elif subject_id not in self.nodes:
            self.report(code="error.edge.subject.missing_from_nodes", object_id=subject_id)
        if self.graph_type is TRAPIGraphType.Knowledge_Graph:
            if not predicate:
                self.report(code="error.edge.predicate.missing", edge_id=edge_id)
            else:
                self.validate_predicate(predicate=predicate, strict_validation=strict_validation)
        else:  # is a Query Graph...
            if predicates is None:
                # Query Graphs can have a missing or null predicates slot
                pass
            elif not isinstance(predicates, List):
                self.report(code="error.edge.predicate.not_array", edge_id=edge_id)
            elif len(predicates) == 0:
                self.report(code="error.edge.predicate.empty_array", edge_id=edge_id)
            else:
                # Should now be a non-empty list of CURIES which are valid Biolink Predicates
                for predicate in predicates:
                    if not predicate:
                        continue  # sanity check
                    self.validate_predicate(predicate=predicate, strict_validation=strict_validation)
        if not object_id:
            self.report(code="error.edge.object.missing", edge_id=edge_id)
        elif object_id not in self.nodes:
            self.report(code="error.edge.object.missing_from_nodes", object_id=object_id)
        if self.graph_type is TRAPIGraphType.Knowledge_Graph:
            self.validate_attributes(edge=edge)
        else:
            # TODO: do we need to validate Query Graph 'constraints' slot contents here?
            pass

    def validate_category(
            self,
            context: str,
            node_id: Optional[str],
            category: Optional[str],
            strict_validation: bool = True
    ) -> ClassDefinition:
        """
        Validate a Biolink category.

        :param context: str, label for context of concept whose category is being validated, i.e. 'Subject' or 'Object'
        :param node_id: str, CURIE of concept node whose category is being validated
        :param category: str, CURIE of putative concept 'category'
        :param strict_validation: if True, abstract and mixin elements validate as 'error'; False, issue 'info' message.
        :return:
        """
        biolink_class: Optional[ClassDefinition] = None
        if category:
            # this method reports unknown Biolink Elements
            biolink_class = self.validate_element_status(
                    context=context,
                    name=category,
                    strict_validation=strict_validation
            )
            if biolink_class and not self.bmt.is_category(category):
                self.report(code="error.node.category.invalid", context=context, category=category)
                biolink_class = None
        else:
            self.report(code="error.node.category.missing", context=context, node_id=node_id)

        return biolink_class

    def validate_input_edge_node(self, context: str, node_id: Optional[str], category: Optional[str]):

        if node_id:
            biolink_class: Optional[ClassDefinition] = self.validate_category(
                context=f"{context}",
                node_id=node_id,
                category=category,
                # we allow 'abstract' and 'mixin' type
                # categories in input query data
                strict_validation=False
            )
            if biolink_class:
                possible_subject_categories = self.bmt.get_element_by_prefix(node_id)
                if biolink_class.name not in possible_subject_categories:
                    self.report(
                        code="warning.node.identifier_unmapped_to_category",
                        context=context,
                        node_id=node_id,
                        category=category
                    )
            # else, we will have already reported an error in validate_category()
        else:
            self.report(code="error.node.missing_identifier", context=context)

    def check_biolink_model_compliance_of_input_edge(self, edge: Dict[str, str], strict_validation: bool = False):
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
        :param strict_validation: if True, abstract and mixin elements validate as 'error'; False, issue 'info' message.
        :type strict_validation: bool = False
        """
        # data fields to be validated...
        subject_category_curie = edge['subject_category'] if 'subject_category' in edge else None
        object_category_curie = edge['object_category'] if 'object_category' in edge else None
        predicate = edge['predicate'] if 'predicate' in edge else None
        subject_curie = edge['subject'] if 'subject' in edge else None
        object_curie = edge['object'] if 'object' in edge else None

        self.validate_input_edge_node(
            context='Subject',
            node_id=subject_curie,
            category=subject_category_curie
        )
        if not predicate:
            self.report(code="error.predicate.missing")
        else:
            self.validate_predicate(predicate=predicate, strict_validation=strict_validation)

        self.validate_input_edge_node(
            context='Object',
            node_id=object_curie,
            category=object_category_curie
        )

    def check_biolink_model_compliance(
            self,
            graph: Dict,
            strict_validation: bool
    ):
        """
        Validate a TRAPI-schema compliant Message graph-like data structure
        against the currently active Biolink Model Toolkit model version.
    
        :param graph: knowledge graph to be validated
        :type graph: Dict
        :param strict_validation: if True, abstract and mixin elements validate as 'error'; False, issue 'info' message.
        :type strict_validation: bool
        """
        if not graph:
            self.report(code="warning.graph.empty", context=self.graph_type)
            return  # nothing really more to do here!

        # Access graph data fields to be validated
        nodes: Optional[Dict]
        if 'nodes' in graph and graph['nodes']:
            nodes = graph['nodes']
        else:
            # Query Graphs can have an empty nodes catalog
            if self.graph_type is not TRAPIGraphType.Query_Graph:
                self.report(code="error.empty_nodes")
            # else:  Query Graphs can omit the 'nodes' tag
            nodes = None

        edges: Optional[Dict]
        if 'edges' in graph and graph['edges']:
            edges = graph['edges']
        else:
            if self.graph_type is not TRAPIGraphType.Query_Graph:
                self.report(code="error.empty_edges")
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
                    self.validate_graph_edge(edge, strict_validation=strict_validation)

                    edges_seen += 1
                    if edges_seen >= _MAX_TEST_EDGES:
                        break


def check_biolink_model_compliance_of_input_edge(
        edge: Dict[str, str],
        biolink_version: Optional[str] = None
) -> BiolinkValidator:
    """
    Validate an (SRI Testing style) input edge record
    against a designated Biolink Model release.

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
    :param biolink_version: Biolink Model (SemVer) release against which the knowledge graph is to be
                            validated (Default: if None, use the Biolink Model Toolkit default version.
    :type biolink_version: Optional[str] = None
    :returns: Biolink Model validator cataloging validation messages (may be empty)
    :rtype: BiolinkValidator
    """
    validator = BiolinkValidator(graph_type=TRAPIGraphType.Edge_Object, biolink_version=biolink_version)
    validator.check_biolink_model_compliance_of_input_edge(edge)
    return validator


def check_biolink_model_compliance_of_query_graph(
        graph: Dict,
        biolink_version: Optional[str] = None,
        strict_validation: bool = False
) -> BiolinkValidator:
    """
    Validate a TRAPI-schema compliant Message Query Graph
    against a designated Biolink Model release.

    Since a Query graph is usually an incomplete knowledge graph specification,
    the validation undertaken is not 'strict'

    :param graph: query graph to be validated
    :type graph: Dict
    :param biolink_version: Biolink Model (SemVer) release against which the knowledge graph is to be
                            validated (Default: if None, use the Biolink Model Toolkit default version.
    :type biolink_version: Optional[str] = None
    :param strict_validation: if True, abstract and mixin elements validate as 'error'; False, issue 'info' message.
    :type strict_validation: bool = False

    :returns: Biolink Model validator cataloging validation messages (may be empty)
    :rtype: BiolinkValidator
    """
    validator = BiolinkValidator(graph_type=TRAPIGraphType.Query_Graph, biolink_version=biolink_version)
    validator.check_biolink_model_compliance(graph, strict_validation)
    return validator


def check_biolink_model_compliance_of_knowledge_graph(
    graph: Dict,
    biolink_version: Optional[str] = None,
    strict_validation: bool = True
) -> BiolinkValidator:
    """
    Strict validation of a TRAPI-schema compliant Message Knowledge Graph
     against a designated Biolink Model release.

    :param graph: knowledge graph to be validated.
    :type graph: Dict
    :param biolink_version: Biolink Model (SemVer) release against which the knowledge graph is to be
                            validated (Default: if None, use the Biolink Model Toolkit default version.
    :type biolink_version: Optional[str] = None
    :param strict_validation: if True, abstract and mixin elements validate as 'error'; False, issue 'info' message.
    :type strict_validation: bool = True

    :returns: Biolink Model validator cataloging validation messages (may be empty)
    :rtype: BiolinkValidator
    """
    validator = BiolinkValidator(graph_type=TRAPIGraphType.Knowledge_Graph, biolink_version=biolink_version)
    validator.check_biolink_model_compliance(graph, strict_validation)
    return validator


def sample_results(results: List) -> List:
    sample_size = min(TEST_DATA_SAMPLE_SIZE, len(results))
    result_subsample = results[0:sample_size]
    return result_subsample


def sample_graph(graph: Dict) -> Dict:
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


def validate_query_graph(validator: ValidationReporter, message: Dict):
    # Query Graph must not be missing...
    if 'query_graph' not in message:
        validator.report(code="error.response.query_graph.missing")
    else:
        # ... nor empty
        query_graph = message['query_graph']
        if not (query_graph and len(query_graph) > 0):
            validator.report(code="error.response.query_graph.empty")
        else:
            # Validate the TRAPI compliance of the Query Graph
            trapi_validator: TRAPIValidator = check_trapi_validity(
                instance=query_graph,
                component="QueryGraph",
                trapi_version=validator.trapi_version
            )
            if trapi_validator.has_messages():
                validator.merge(trapi_validator)

            # Validate the Biolink Model compliance of the Query Graph
            biolink_validator = check_biolink_model_compliance_of_query_graph(
                graph=query_graph,
                biolink_version=validator.biolink_version
            )
            if biolink_validator.has_messages():
                validator.merge(biolink_validator)


def validate_knowledge_graph(validator: ValidationReporter, message: Dict):
    # The Knowledge Graph should not be missing
    if 'knowledge_graph' not in message:
        validator.report(code="error.response.knowledge_graph.missing")
    else:
        knowledge_graph = message['knowledge_graph']
        # The Knowledge Graph should also not generally be empty? Issue a warning
        if not (
                knowledge_graph and len(knowledge_graph) > 0 and
                "nodes" in knowledge_graph and len(knowledge_graph["nodes"]) > 0 and
                "edges" in knowledge_graph and len(knowledge_graph["edges"]) > 0
        ):
            validator.report(code="warning.response.knowledge_graph.empty")
        else:
            mapping_validator: ValidationReporter = check_node_edge_mappings(knowledge_graph)
            if mapping_validator.has_messages():
                validator.merge(mapping_validator)

            # ...then if not empty, validate a subgraph sample of the associated
            # Knowledge Graph (since some TRAPI response kg's may be huge!)
            kg_sample = sample_graph(knowledge_graph)

            # Verify that the sample of the knowledge graph is TRAPI compliant
            trapi_validator: TRAPIValidator = check_trapi_validity(
                instance=kg_sample,
                component="KnowledgeGraph",
                trapi_version=validator.trapi_version
            )
            if trapi_validator.has_messages():
                validator.merge(trapi_validator)

            # Verify that the sample of the knowledge graph is
            # compliant to the currently applicable Biolink Model release
            biolink_validator = check_biolink_model_compliance_of_knowledge_graph(
                graph=kg_sample,
                biolink_version=validator.biolink_version
            )
            if biolink_validator.has_messages():
                validator.merge(biolink_validator)


def validate_results(validator: ValidationReporter, message: Dict):

    #     :param output_element: test target, as edge 'subject' or 'object'
    #     :type output_element: str
    #     :param output_node_binding: node 'a' or 'b' of the ('one hop') QGraph test query
    #     :type output_node_binding: str
    # The Knowledge Graph should not be missing
    if 'results' not in message:
        validator.report(code="error.response.results.missing")
    else:
        results = message['results']
        if not (results and len(results) > 0):
            # The Message.results should not generally be None or empty?
            validator.report(code="warning.response.results.empty")
        elif not isinstance(results, List):
            # The Message.results should be an array of Result objects
            validator.report(code="error.response.results.non_array")
        else:
            # Validate a subsample of a non-empty Message.results component.
            results_sample = sample_results(results)
            for result in results_sample:
                trapi_validator: TRAPIValidator = check_trapi_validity(
                    instance=result,
                    component="Result",
                    trapi_version=validator.trapi_version
                )
                if trapi_validator.has_messages():
                    # Record the error messages associated with the Result set then... don't continue
                    validator.merge(trapi_validator)
                    return validator

                # TODO: here, we might wish to compare the Results against the contents of the KnowledgeGraph,
                #       with respect to node input values from the QueryGraph but this is tricky to do solely
                #       with the subsamples, which may not completely overlap.

                # ...Finally, check that the sample Results contained the object of the Query

                # The 'output_element' is 'subject' or 'object' target (unknown) of retrieval
                # The 'output_node_binding' is (subject) 'a' or (object) 'b' keys in the QueryGraph.Nodes to be bound
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


def check_biolink_model_compliance_of_trapi_response(
    message: Dict,
    trapi_version: str,
    biolink_version: Optional[str] = None
) -> ValidationReporter:
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
    :param trapi_version: version of component against which to validate the message (mandatory, no default assumed).
    :type trapi_version: str
    :param biolink_version: Biolink Model (SemVer) release against which the knowledge graph is to be
                            validated (Default: if None, use the Biolink Model Toolkit default version.
    :type biolink_version: Optional[str] = None

    :returns: Validator cataloging "information", "warning" and "error" messages (may be empty)
    :rtype: ValidationReporter
    """
    validator: ValidationReporter = ValidationReporter(
        prefix="Validate TRAPI Response",
        trapi_version=trapi_version,
        biolink_version=biolink_version
    )
    if not message:
        validator.report("error.response.message.empty")
    # Sequentially validate the Query Graph, Knowledge Graph then validate
    # the Results (which rely on the validity of the other two components)
    elif validator.apply_validation(validate_query_graph, message) and \
            validator.apply_validation(validate_knowledge_graph, message):
        validator.apply_validation(validate_results, message)

    return validator
