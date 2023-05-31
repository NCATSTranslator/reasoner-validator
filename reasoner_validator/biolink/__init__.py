"""
Version-specific Biolink Model semantic validation of knowledge graph components.
"""
from typing import Optional, Any, Dict, List, Tuple, Set
from enum import Enum
from functools import lru_cache
from urllib.error import HTTPError
from pprint import PrettyPrinter


from bmt import Toolkit
from bmt.utils import parse_name
from linkml_runtime.linkml_model import ClassDefinition, Element

from reasoner_validator.sri.util import is_curie
from reasoner_validator.report import ValidationReporter
from reasoner_validator.versioning import SemVer, SemVerError

import logging
logger = logging.getLogger(__name__)

pp = PrettyPrinter(indent=4)


def _get_biolink_model_schema(biolink_version: Optional[str] = None) -> Optional[str]:
    # Get Biolink Model Schema
    if biolink_version:
        try:
            svm = SemVer.from_string(biolink_version)

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
    Input_Edge = "Input Edge"
    Query_Graph = "Query Graph"
    Knowledge_Graph = "Knowledge Graph"


class BiolinkValidator(ValidationReporter):
    """
    Wrapper class for Biolink Model validation.
    """
    def __init__(
        self,
        graph_type: TRAPIGraphType,
        trapi_version: Optional[str] = None,
        biolink_version: Optional[str] = None,
        sources: Optional[Dict[str, str]] = None,
        strict_validation: bool = False
    ):
        """
        Biolink Validator constructor.

        :param graph_type: type of graph data being validated
        :type graph_type: TRAPIGraphType
        :param trapi_version: caller specified Biolink Model version (default: None, which takes the TRAPI 'latest')
        :type trapi_version: Optional[str] or None
        :param biolink_version: caller specified Biolink Model version (default: None, which takes the BMT 'latest')
        :type biolink_version: Optional[str] or None
        :param sources: Dictionary of validation context identifying the ARA and KP for provenance attribute validation
        :type sources: Optional[Dict[str,str]]
        """
        self.bmt: Toolkit = get_biolink_model_toolkit(biolink_version=biolink_version)
        resolved_biolink_version = self.bmt.get_model_version()
        ValidationReporter.__init__(
            self,
            prefix=f"Biolink Validation of {graph_type.value}",
            trapi_version=trapi_version,
            biolink_version=resolved_biolink_version,
            sources=sources,
            strict_validation=strict_validation
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

    def get_result(self) -> Tuple[str, Optional[Dict[str, Dict[str, Optional[List[Dict[str, str]]]]]]]:
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
                    self.report(code="error.knowledge_graph.node.categories.not_array", identifier=node_id)
                else:
                    categories = slots["categories"]
                    node_prefix_mapped: bool = False
                    concrete_category_found: bool = False
                    for category in categories:
                        category: Optional[ClassDefinition] = \
                            self.validate_category(
                                context="knowledge_graph",
                                node_id=node_id,
                                category=category
                            )
                        # Only 'concrete' (non-abstract, non-mixin, preferably,
                        # non-deprecated) categories are of interest here,
                        # since only they will have associated namespaces
                        if category:
                            concrete_category_found: bool = True
                            possible_subject_categories = self.bmt.get_element_by_prefix(node_id)
                            if possible_subject_categories and category.name in possible_subject_categories:
                                node_prefix_mapped = True
                                # don't need to search any more categories
                                break

                    if not concrete_category_found:
                        self.report(
                            code="error.knowledge_graph.node.categories.not_concrete",
                            identifier=node_id,
                            categories=str(categories)
                        )

                    if not node_prefix_mapped:
                        self.report(
                            code="warning.knowledge_graph.node.id.unmapped_prefix",
                            identifier=node_id,
                            categories=str(categories)
                        )
            else:
                self.report(
                    code="error.knowledge_graph.node.category.missing",
                    context=self.graph_type.value, identifier=node_id
                )

            # TODO: Do we need to (or can we) validate here, any other
            #       Knowledge Graph node fields? Perhaps not yet?

        else:  # Query Graph node validation

            has_node_ids: bool
            if "ids" in slots and slots["ids"]:
                has_node_ids = True
                node_ids = slots["ids"]
                if isinstance(node_ids, List):
                    # because the validation below is destructive
                    # to node_ids, we copy the original list
                    node_ids = node_ids.copy()
                else:
                    self.report(code="error.query_graph.node.ids.not_array", identifier=node_id)
                    # we'll pretend that the ids were mistakenly
                    # just a scalar string, then continue validating
                    node_ids = [str(node_ids)]
            else:
                has_node_ids = False
                node_ids = list()  # a null "ids" value is permitted in QNodes

            if "categories" in slots:
                categories = slots["categories"]
                if categories:
                    if not isinstance(categories, List):
                        self.report(code="error.query_graph.node.categories.not_array", identifier=node_id)
                    else:
                        id_prefix_mapped: Dict = {identifier: False for identifier in node_ids}
                        for category in categories:
                            category: Optional[ClassDefinition] = \
                                self.validate_category(
                                    context="query_graph",
                                    node_id=node_id,
                                    category=category
                                )
                            # Only 'concrete' (non-abstract, non-mixin, preferably, non-deprecated)
                            # categories will be tested here for identifier namespaces.  Also, we
                            # actually don't care if Query Graphs don't have at least one concrete category...
                            if category:
                                for identifier in node_ids:  # may be empty list if not provided...
                                    possible_subject_categories = self.bmt.get_element_by_prefix(identifier)
                                    if category.name in possible_subject_categories:
                                        id_prefix_mapped[identifier] = True
                                        node_ids.remove(identifier)
                                        # found a suitable mapping for the given identifier
                                        break

                        # At this point, if any 'node_ids' are NOT
                        # removed (above), then they are unmapped
                        if has_node_ids and node_ids:
                            self.report(
                                code="warning.query_graph.node.ids.unmapped_prefix",
                                identifier=node_id,
                                unmapped_ids=str(node_ids),
                                categories=str(categories)
                            )

                # else:  # null "categories" value is permitted in QNodes by nullable: true
            # else:  # missing "categories" key is permitted in QNodes by nullable: true

            if 'is_set' in slots:
                is_set = slots["is_set"]
                if is_set and not isinstance(is_set, bool):
                    self.report(code="error.query_graph.node.is_set.not_boolean", identifier=node_id)
            # else:  # a missing key or null "is_set" value is permitted in QNodes but defaults to 'False'

            # constraints  # TODO: how do we validate node constraints?
            pass

    def set_nodes(self, nodes: Set):
        self.nodes.update(nodes)

    def validate_element_status(self, context: str, identifier: str, edge_id: str) -> Optional[Element]:
        """
        Detect element missing from Biolink, or is deprecated, abstract or mixin, signalled as a failure or warning.

        :param context: str, parsing context (e.g. 'Node')
        :param identifier: str, name of the putative Biolink element ('class')
        :param edge_id: str, identifier of enclosing edge containing the element (e.g. the 'edge_id')

        :return: Optional[Element], Biolink Element resolved to 'name' if element no validation error; None otherwise.
        """
        element: Optional[Element] = self.bmt.get_element(identifier)
        if not element:
            self.report(code=f"error.{context}.unknown", identifier=identifier, edge_id=edge_id)
            return None

        if element.deprecated:
            # We won't index the instances where the deprecated element is seen, since we assume that
            # component developers learning about the issue will globally fix it in their graphs
            self.report(code=f"warning.{context}.deprecated", identifier=identifier)
            # return None - a deprecated term is not treated as a failure but just as a warning

        if element.abstract:
            if self.strict_validation:
                self.report(code=f"error.{context}.abstract", identifier=identifier, edge_id=edge_id)
                return None
            else:
                self.report(code=f"info.{context}.abstract", identifier=identifier, edge_id=edge_id)

        elif self.bmt.is_mixin(identifier):
            # A mixin cannot be instantiated ...
            if self.strict_validation:
                self.report(code=f"error.{context}.mixin", identifier=identifier, edge_id=edge_id)
                return None
            else:
                self.report(code=f"info.{context}.mixin", identifier=identifier, edge_id=edge_id)

        return element

    def get_target_sources(self) -> Tuple[Optional[str], Optional[str], Optional[str]]:
        """
        Returns infores prefix normalized validation caller provided tTarget provenance sources metadata.
        :return: Tuple[Optional[str], Optional[str], Optional[str]] of ara_source, kp_source, kp_source_type
        """
        ara_source: Optional[str] = None
        kp_source: Optional[str] = None
        kp_source_type: Optional[str] = None
        if self.sources:
            if 'ara_source' in self.sources and self.sources['ara_source']:
                ara_source: str = self.sources['ara_source']
                if not ara_source.startswith("infores:"):
                    ara_source = f"infores:{ara_source}"
            if 'kp_source' in self.sources and self.sources['kp_source']:
                kp_source: str = self.sources['kp_source']
                if not kp_source.startswith("infores:"):
                    kp_source = f"infores:{kp_source}"
            kp_source_type = self.sources['kp_source_type'] \
                if 'kp_source_type' in self.sources and self.sources['kp_source_type'] else 'aggregator'
            kp_source_type = f"biolink:{kp_source_type}_knowledge_source"

        return ara_source, kp_source, kp_source_type

    def validate_provenance(
            self,
            edge_id,
            ara_source, found_ara_knowledge_source,
            kp_source, found_kp_knowledge_source, kp_source_type,
            found_primary_knowledge_source
    ):
        """
        Validates ARA and KP sources based on surveyed Edge slots (in 'attributes' pre-1.4.0; in 'sources', post-1.4.0).

        :param edge_id: str, string identifier for the edge (for reporting purposes)
        :param ara_source: str, user specified target ARA infores
        :param found_ara_knowledge_source: bool, True if target ARA infores knowledge source was found
        :param kp_source: str, user specified target KP infores
        :param found_kp_knowledge_source:  bool, True if target KP infores knowledge source was found
        :param kp_source_type:  str, user specified KP knowledge source type (i.e. primary, aggregate, etc.)
        :param found_primary_knowledge_source: List[str], list of all infores discovered tagged as 'primary'
        :return:
        """
        if ara_source and not found_ara_knowledge_source:
            # found target ARA knowledge source (if applicable)
            self.report(
                code="warning.knowledge_graph.edge.provenance.ara.missing",
                identifier=ara_source,
                edge_id=edge_id
            )

        if kp_source and not found_kp_knowledge_source:
            # found target KP knowledge source (if applicable)
            self.report(
                code="warning.knowledge_graph.edge.provenance.kp.missing",
                identifier=kp_source,
                kp_source_type=kp_source_type,
                identedge_idifier=edge_id
            )

        if not found_primary_knowledge_source:
            # Found a primary tagged source...
            self.report(
                code="error.knowledge_graph.edge.provenance.missing_primary",
                identifier=edge_id
            )
        elif len(found_primary_knowledge_source) > 1:
            # ... but only one!
            self.report(
                code="warning.knowledge_graph.edge.provenance.multiple_primary",
                identifier=edge_id,
                sources=",".join(found_primary_knowledge_source)
            )

    def validate_attributes(self, edge_id: str, edge: Dict):
        """
        Validate Knowledge Edge Attributes.

        :param edge_id: str, string identifier for the edge (for reporting purposes)
        :param edge: Dict, the edge object associated with some attributes are expected to be found
        :return: None (validation messages captured in the 'self' BiolinkValidator context)
        """
        # we only report errors about missing or empty edge attributes if TRAPI 1.3.0 or earlier,
        # since earlier TRAPI releases are minimally expected to record provenance attributes
        if 'attributes' not in edge:
            if not self.minimum_required_trapi_version("1.4.0-beta"):
                self.report(code="error.knowledge_graph.edge.attribute.missing", identifier=edge_id)
        elif not edge['attributes']:
            if not self.minimum_required_trapi_version("1.4.0-beta"):
                self.report(code="error.knowledge_graph.edge.attribute.empty", identifier=edge_id)
        elif not isinstance(edge['attributes'], List):
            self.report(code="error.knowledge_graph.edge.attribute.not_array", identifier=edge_id)
        else:
            attributes = edge['attributes']

            ara_source: Optional[str]
            kp_source: Optional[str]
            kp_source_type: Optional[str]
            ara_source, kp_source, kp_source_type = self.get_target_sources()

            # Expecting ARA and KP 'aggregator_knowledge_source' attributes?
            found_ara_knowledge_source = False
            found_kp_knowledge_source = False

            # also track primary_knowledge_source attribute cardinality now
            found_primary_knowledge_source: List[str] = list()

            for attribute in attributes:

                # Validate attribute_type_id
                if 'attribute_type_id' not in attribute:
                    self.report(
                        code="error.knowledge_graph.edge.attribute.type_id.missing",
                        identifier=edge_id
                    )
                elif not attribute['attribute_type_id']:
                    self.report(
                        code="error.knowledge_graph.edge.attribute.type_id.empty",
                        identifier=edge_id
                    )
                elif 'value' not in attribute:
                    self.report(
                        code="error.knowledge_graph.edge.attribute.value.missing",
                        identifier=edge_id
                    )
                elif not attribute['value'] or \
                        str(attribute['value']).upper() in ["N/A","NONE","NULL"]:
                    self.report(
                        code="error.knowledge_graph.edge.attribute.value.empty",
                        identifier=edge_id
                    )
                else:
                    attribute_type_id: str = attribute['attribute_type_id']
                    value = attribute['value']

                    # TODO: there seems to be non-uniformity in provenance attribute values for some KP/ARA's
                    #       in which a value is returned as a Python list (of at least one element?) instead
                    #       of a string. Here, to ensure full coverage of the attribute values returned,
                    #       we'll coerce scalar values into a list, then iterate.
                    if not isinstance(value, List):
                        value = [value]

                    if not is_curie(attribute_type_id):
                        self.report(
                            code="error.knowledge_graph.edge.attribute.type_id.not_curie",
                            identifier=attribute_type_id,
                            edge_id=edge_id
                        )
                    else:
                        # 'attribute_type_id' is a CURIE, but how well does it map?
                        prefix = attribute_type_id.split(":", 1)[0]
                        if prefix == 'biolink':
                            biolink_class = self.validate_element_status(
                                context="knowledge_graph.edge.attribute.type_id",
                                identifier=attribute_type_id,
                                edge_id=edge_id
                            )
                            if biolink_class:
                                if not self.bmt.is_association_slot(attribute_type_id):
                                    self.report(
                                        code="warning.knowledge_graph.edge.attribute.type_id.not_association_slot",
                                        identifier=attribute_type_id,
                                        edge_id=edge_id
                                    )

                                else:
                                    # it is a Biolink 'association_slot' but now, validate what kind?

                                    # TODO: only check knowledge_source provenance here for now.
                                    #       Are there other association_slots to be validated here too?

                                    # Edge provenance tags only recorded in Edge attributes prior to TRAPI 1.4.0-beta
                                    if not self.minimum_required_trapi_version("1.4.0-beta"):

                                        if attribute_type_id not in \
                                                [
                                                    "biolink:aggregator_knowledge_source",
                                                    "biolink:primary_knowledge_source",

                                                    # Note: deprecated since Biolink release 3.0.2
                                                    #       but this is probably caught above in the
                                                    #       'validate_element_status' method predicate
                                                    "biolink:original_knowledge_source"

                                                ]:

                                            # TODO: not interested here in any other
                                            #       attribute_type_id's at this moment
                                            continue

                                        # ... now, check the infores values against various expectations
                                        for infores in value:
                                            if not infores.startswith("infores:"):
                                                self.report(
                                                    code="error.knowledge_graph.edge.provenance.infores.missing",
                                                    identifier=str(infores),
                                                    edge_id=edge_id
                                                )
                                            else:
                                                if attribute_type_id == "biolink:primary_knowledge_source":
                                                    found_primary_knowledge_source.append(infores)

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
                                code="warning.knowledge_graph.edge.attribute.type_id.unknown_prefix",
                                identifier=attribute_type_id,
                                edge_id=edge_id
                            )
                        # TODO: probably need to take a closer look at validating outlier terms here
                        #       Maybe enumerations will help
                        else:
                            self.report(
                                code="info.knowledge_graph.edge.attribute.type_id.non_biolink_prefix",
                                identifier=attribute_type_id,
                                edge_id=edge_id
                            )

            # Edge provenance tags only recorded in Edge attributes prior to TRAPI 1.4.0-beta
            if not self.minimum_required_trapi_version("1.4.0-beta"):

                # TODO: After all the attributes have been scanned,
                #       check for provenance. Treat as warnings for now.
                self.validate_provenance(
                    edge_id,
                    ara_source, found_ara_knowledge_source,
                    kp_source, found_kp_knowledge_source, kp_source_type,
                    found_primary_knowledge_source
                )

    def validate_attribute_constraints(self, edge_id: str, edge: Dict):
        """
        Validate Query Edge Attributes.

        :param edge_id: str, string identifier for the edge (for reporting purposes)
        :param edge: Dict, the edge object associated with some attributes are expected to be found
        :return: None (validation messages captured in the 'self' BiolinkValidator context)
        """
        if 'attribute_constraints' not in edge or edge['attribute_constraints'] is None:
            return  # nullable: true... missing key or None value is ok?
        elif not isinstance(edge['attribute_constraints'], List):
            self.report(code="error.query_graph.edge.attribute_constraints.not_array", identifier=edge_id)
        elif not edge['attribute_constraints']:
            return  # nullable: true... an empty 'attribute_constraints' array is ok?
        else:
            # TODO: not yet sure what else to do here (if anything...yet)
            attribute_constraints: List = edge['attribute_constraints']

    def validate_qualifier_entry(self, context: str, edge_id: str, qualifiers: List[Dict[str, str]]):
        """
        Validate Qualifier Entry (JSON Object).

        :param context: str, Validation (subcode) context:
                        - query graph qualifier constraints ("query_graph.edge.qualifier_constraints.qualifier_set") or
                        - knowledge graph edge qualifiers (knowledge_graph.edge.qualifiers)
        :param edge_id: str, string identifier for the edge (for reporting purposes)
        :param qualifiers: List[Dict[str, str]], of qualifier entries to be validated.
        :return: None (validation messages captured in the 'self' BiolinkValidator context)
        """
        for qualifier in qualifiers:
            qualifier_type_id: str = qualifier['qualifier_type_id']
            qualifier_value: str = qualifier['qualifier_value']
            try:
                if not self.bmt.is_qualifier(name=qualifier_type_id):
                    self.report(
                        code=f"error.{context}.qualifier.type_id.unknown",
                        identifier=qualifier_type_id,
                        edge_id=edge_id
                    )
                elif qualifier_type_id == "biolink:qualified_predicate":
                    if not self.bmt.is_predicate(qualifier_value):
                        # special case of qualifier must have Biolink predicates as values
                        self.report(
                            code=f"error.{context}.qualifier.value.not_a_predicate",
                            identifier=qualifier_value,
                            edge_id=edge_id
                        )

                # A Query Graph miss on qualifier_value is less an issue since there may not be enough
                # context to resolve the 'qualifier_value'; whereas a Knowledge Graph miss is more severe
                # TODO: however, we somehow need to leverage TRAPI MetaEdge.association metadata here?
                elif context.startswith("knowledge_graph") and not self.bmt.validate_qualifier(
                        qualifier_type_id=qualifier_type_id,
                        qualifier_value=qualifier_value
                ):
                    self.report(
                        code=f"error.{context}.qualifier.value.unresolved",
                        identifier=qualifier_value,
                        edge_id=edge_id,
                        qualifier_type_id=qualifier_type_id
                    )
            except Exception as e:
                # broad spectrum exception to trap anticipated short term issues with BMT validation
                logger.error(f"BMT validate_qualifier Exception: {str(e)}")
                self.report(
                    code=f"error.{context}.qualifier.invalid",
                    identifier=edge_id,
                    qualifier_type_id=qualifier_type_id,
                    qualifier_value=qualifier_value,
                    reason=str(e)
                )

    def validate_qualifiers(self, edge_id: str, edge: Dict):
        """
        Validate Knowledge Edge Qualifiers.

        :param edge_id: str, string identifier for the edge (for reporting purposes)
        :param edge: Dict, the edge object associated with some attributes are expected to be found
        :return: None (validation messages captured in the 'self' BiolinkValidator context)
        """
        # Edge qualifiers will only be seen in Biolink 3 data,
        # but with missing 'qualifiers', no validation is attempted
        if 'qualifiers' not in edge or edge['qualifiers'] is None:
            return  # nullable: true... missing key or None value is ok?
        elif not isinstance(edge['qualifiers'], List):
            self.report(code="error.knowledge_graph.edge.qualifiers.not_array", identifier=edge_id)
        elif not edge['qualifiers']:
            return  # nullable: true... an empty 'qualifiers' array is ok?
        else:
            qualifiers: List = edge['qualifiers']
            self.validate_qualifier_entry(
                context="knowledge_graph.edge.qualifiers",
                edge_id=edge_id,
                qualifiers=qualifiers
            )

    def validate_qualifier_constraints(self, edge_id: str, edge: Dict):
        """
        Validate Query Edge Qualifier Constraints.

        :param edge_id: str, string identifier for the edge (for reporting purposes)
        :param edge: Dict, the edge object associated with some attributes are expected to be found
        :return: None (validation messages captured in the 'self' BiolinkValidator context)
        """
        # Edge qualifiers will only be seen in Biolink 3 data,
        # but with missing 'qualifier_constraints', no validation is attempted
        if 'qualifier_constraints' not in edge or edge['qualifier_constraints'] is None:
            return  # nullable: true... missing key or None value is ok?
        elif not edge['qualifier_constraints']:
            return  # nullable: true... an empty 'qualifier_constraints' array is ok?
        else:
            # we have putative 'qualifier_constraints'
            qualifier_constraints: List = edge['qualifier_constraints']
            for qualifier_set_entry in qualifier_constraints:
                # An entry in the 'qualifier_constraints' array is mandatory to be non-empty
                # and a dictionary, if qualifier_constraints is not empty
                # Mandatory tag in every 'qualifier_constraint' entry
                if not qualifier_set_entry['qualifier_set']:
                    self.report(
                        code="error.query_graph.edge.qualifier_constraints.qualifier_set.empty",
                        identifier=edge_id
                    )
                else:
                    # We have a putative non-empty 'qualifier_set'
                    qualifier_set: List = qualifier_set_entry['qualifier_set']
                    self.validate_qualifier_entry(
                        context="query_graph.edge.qualifier_constraints.qualifier_set",
                        edge_id=edge_id,
                        qualifiers=qualifier_set
                    )

    def validate_infores(self, context: str, edge_id: str, identifier: str):
        code_prefix: str = f"error.knowledge_graph.edge.sources.retrieval_source.{context}.infores"
        if not is_curie(identifier):
            self.report(
                code=f"{code_prefix}.not_curie",
                identifier=identifier,
                edge_id=edge_id
            )
        elif not identifier.startswith("infores:"):
            # not sure how absolute the need is for this to be an Infores. We'll be lenient for now?
            self.report(
                code=f"{code_prefix}.invalid",
                identifier=identifier,
                edge_id=edge_id
            )
        # TODO: infores is causing too much instability for now so support has been removed from BMT
        # TODO: reimplement using YAML version of infores catalog
        # elif not self.bmt.get_infores_details(identifier):
        #     # if this method returns 'None' then this is an unregistered infores?
        #     self.report(
        #         code=f"{code_prefix}.unknown",
        #         identifier=identifier,
        #         edge_id=edge_id
        #     )

    def validate_sources(self, edge_id: str, edge: Dict):
        """
        Validate (TRAPI 1.4.0-beta ++) Edge.sources provenance.

        :param edge_id: str, string identifier for the edge (for reporting purposes)
        :param edge: Dict, the edge object associated with some attributes are expected to be found
        :return: None (validation messages captured in the 'self' BiolinkValidator context)
        """
        # we ought not to have to test for the absence of the 'sources' tag
        # if general TRAPI schema validation is run, since it will catch such missing data
        # however, this method may be directly run on invalid TRAPI data, so...
        if 'sources' not in edge:
            self.report(code="error.knowledge_graph.edge.sources.missing", identifier=edge_id)
        elif not edge['sources']:
            # Cardinality of 'sources' array is also validated by the TRAPI schema
            # but for the same reasons noted above, we check again here.
            self.report(code="error.knowledge_graph.edge.sources.empty", identifier=edge_id)
        elif not isinstance(edge['sources'], List):
            self.report(code="error.knowledge_graph.edge.sources.not_array", identifier=edge_id)
        else:
            edge_sources = edge['sources']

            # The RetrievalSource items in the 'sources' array is also partially validated insofar as JSONSchema can
            # validate based on the TRAPI schema; however, some kinds of validation are either not deterministic from
            # the schema. The remainder of this method validates an initial basic 'semantic' subset of RetrievalSource
            # content for which the validation is both easy and deemed generally useful. This includes detection of
            # anticipated Edge provenance roles (i.e. mandatory 'primary' and tests against expected provenance tags)

            # Method caller associated Edge sources to be checked

            ara_source: Optional[str]
            kp_source: Optional[str]
            kp_source_type: Optional[str]
            ara_source, kp_source, kp_source_type = self.get_target_sources()

            # Expecting ARA and KP 'aggregator_knowledge_source' attributes?
            found_ara_knowledge_source = False
            found_kp_knowledge_source = False

            # also track primary_knowledge_source attribute cardinality now
            found_primary_knowledge_source: List[str] = list()

            for retrieval_source in edge_sources:

                # TRAPI schema validation will generally validate the requisite
                # 'RetrievalSource' entries (i.e. mandatory object keys and valid key value
                # data types), but here, we go the last (semantic) mile, for the model:

                # 1. 'resource_id': should be a well-formed CURIE which is an Infores which may
                #    include one of the expected Infores entries (from target sources noted above)
                if not ("resource_id" in retrieval_source and retrieval_source["resource_id"]):
                    self.report(
                        code="error.knowledge_graph.edge.sources.retrieval_source.resource_id.empty",
                        identifier=edge_id
                    )
                    continue
                elif not ("resource_role" in retrieval_source and retrieval_source["resource_role"]):
                    # TODO: check if this is ever encountered... maybe TRAPI validation already catches it earlier?
                    self.report(
                        code="error.knowledge_graph.edge.sources.retrieval_source.resource_role.empty",
                        identifier=edge_id
                    )
                    continue

                resource_id: str = retrieval_source["resource_id"]
                resource_role: str = retrieval_source["resource_role"]
                self. validate_infores(context="resource_id", edge_id=edge_id, identifier=resource_id)
                if resource_id == ara_source:
                    found_ara_knowledge_source = True
                if resource_id == kp_source and resource_role == kp_source_type:
                    found_kp_knowledge_source = True

                # ... even if the resource_id fails aspects of validation, we'll keep going...

                # 2. 'resource_role': will have already been TRAPI validated, but is at least one
                #    (but only one?) of 'RetrievalSource' entries the mandatory 'primary'?
                if resource_id and resource_role == "primary_knowledge_source":
                    # the cardinality of this will be checked below...
                    found_primary_knowledge_source.append(resource_id)

                # 3. If provided (Optional), are all 'upstream_resource_ids' well-formed Infores CURIES
                #    and may include some expected Infores entries (from target sources noted above)?
                if "upstream_resource_ids" in retrieval_source:
                    upstream_resource_ids: Optional[List[str]] = retrieval_source["upstream_resource_ids"]
                    # Note: the TRAPI schema doesn't currently tag this field as nullable, so we check
                    if upstream_resource_ids:
                        for identifier in upstream_resource_ids:
                            self.validate_infores(
                                context="upstream_resource_ids",
                                edge_id=edge_id,
                                identifier=identifier
                            )
                            if resource_id == ara_source:
                                found_ara_knowledge_source = True

                            # we don't worry about kp_source_type here since it is
                            # not directly annotated with the upstream_resource_ids
                            if resource_id == kp_source:
                                found_kp_knowledge_source = True

                # 4. If provided (Optional), we *could* check the optional 'source_record_urls'
                #    if they are all resolvable URLs (but maybe we do not attempt this for now...)
                #
                # if "source_record_urls" in retrieval_source:
                #     source_record_urls: Optional[List[str]] = retrieval_source["source_record_urls"]

            # TODO: After all the 'sources' RetrievalSource entries have been scanned, then
            #       perform a complete validation check for complete expected provenance.
            self.validate_provenance(
                edge_id,
                ara_source, found_ara_knowledge_source,
                kp_source, found_kp_knowledge_source, kp_source_type,
                found_primary_knowledge_source
            )

    def validate_predicate(self, edge_id: str, predicate: str):
        """
        :param edge_id: identifier of the edge whose predicate is being validated
        :param predicate: putative Biolink Model predicate to be validated
        :return:
        """
        graph_type_context: str = self.graph_type.name.lower()
        if graph_type_context != "input_edge":
            graph_type_context += ".edge"
        context: str = f"{graph_type_context}.predicate"

        # Validate the putative predicate as *not* being abstract, deprecated or a mixin
        biolink_class = self.validate_element_status(
            context=context,
            identifier=predicate,
            edge_id=edge_id
        )
        if biolink_class:
            if not self.bmt.is_predicate(predicate):
                self.report(
                    code=f"error.{context}.invalid",
                    identifier=predicate,
                    edge_id=edge_id
                )
            elif self.minimum_required_biolink_version("2.2.0") and \
                    not self.bmt.is_translator_canonical_predicate(predicate):
                self.report(
                    code=f"warning.{context}.non_canonical",
                    identifier=predicate,
                    edge_id=edge_id
                )

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
        if self.graph_type is TRAPIGraphType.Knowledge_Graph:
            predicate = edge['predicate'] if 'predicate' in edge else None
            edge_label = predicate
        else:
            # Query Graph...
            predicates = edge['predicates'] if 'predicates' in edge else None
            edge_label = str(predicates)

        object_id = edge['object'] if 'object' in edge else None

        edge_id = f"{str(subject_id)}--{edge_label}->{str(object_id)}"

        context: str = self.graph_type.name.lower()

        # Validate Subject node
        if not subject_id:
            self.report(code=f"error.{context}.edge.subject.missing", identifier=edge_id)

        elif subject_id not in self.nodes:
            self.report(
                code=f"error.{context}.edge.subject.missing_from_nodes",
                identifier=subject_id,
                edge_id=edge_id
            )

        # Validate Predicates
        if self.graph_type is TRAPIGraphType.Knowledge_Graph:
            if not predicate:
                self.report(
                    code="error.knowledge_graph.edge.predicate.missing",
                    context=self.graph_type.value,
                    identifier=edge_id
                )
            else:
                self.validate_predicate(edge_id=edge_id, predicate=predicate)
        else:  # is a Query Graph...
            if predicates is None:
                # Query Graphs can have a missing or null predicates slot
                pass
            elif not isinstance(predicates, List):
                self.report(code="error.query_graph.edge.predicate.not_array", identifier=edge_id)
            elif len(predicates) == 0:
                self.report(code="error.query_graph.edge.predicate.empty_array", identifier=edge_id)
            else:
                # Should now be a non-empty list of CURIES which are valid Biolink Predicates
                for predicate in predicates:
                    if not predicate:
                        continue  # sanity check
                    self.validate_predicate(edge_id=edge_id, predicate=predicate)

        # Validate Object Node
        if not object_id:
            self.report(code=f"error.{context}.edge.object.missing", identifier=edge_id)
        elif object_id not in self.nodes:
            self.report(
                code=f"error.{context}.edge.object.missing_from_nodes",
                identifier=object_id,
                edge_id=edge_id
            )

        # Validate edge attributes (or attribute_constraints)
        # and (Biolink 3) edge qualifiers (or qualifier_constraints)
        if self.graph_type is TRAPIGraphType.Knowledge_Graph:
            self.validate_attributes(edge_id=edge_id, edge=edge)
            self.validate_qualifiers(edge_id=edge_id, edge=edge)

            # Edge provenance 'sources' field is only recorded in
            # Edge attributes, from TRAPI 1.4.0-beta onwards
            if self.minimum_required_trapi_version("1.4.0-beta"):
                self.validate_sources(edge_id=edge_id, edge=edge)
        else:
            self.validate_attribute_constraints(edge_id=edge_id, edge=edge)
            self.validate_qualifier_constraints(edge_id=edge_id, edge=edge)

    def validate_category(
            self,
            context: str,
            node_id: Optional[str],
            category: Optional[str]
    ) -> ClassDefinition:
        """
        Validate a Biolink category.

        Only returns a non-None value if it is a 'concrete' category, and reports 'unknown' or 'missing'
        (None or empty string) category names as errors; deprecated categories are reported as warnings;
        but both 'mixin' and 'abstract' categories are accepted as valid categories silently ignored,
        but are not considered 'concrete', thus the method returns None.

        :param context: str, label for context of concept whose category is being validated, i.e. 'Subject' or 'Object'
        :param node_id: str, CURIE of concept node whose category is being validated
        :param category: str, CURIE of putative concept 'category'

        :return: category as a ClassDefinition, only returned if 'concrete'; None otherwise.
        """
        biolink_class: Optional[ClassDefinition] = None
        if category:
            biolink_class = self.bmt.get_element(category)
            if biolink_class:
                if biolink_class.deprecated:
                    self.report(
                        code=f"warning.{context}.node.category.deprecated",
                        identifier=category,
                        node_id=node_id
                    )
                if biolink_class.abstract or self.bmt.is_mixin(category):
                    biolink_class = None
                elif not self.bmt.is_category(category):
                    self.report(
                        code=f"error.{context}.node.category.not_a_category",
                        identifier=category,
                        node_id=node_id
                    )
                    biolink_class = None
            else:
                self.report(
                    code=f"error.{context}.node.category.unknown",
                    identifier=category,
                    node_id=node_id
                )
        else:
            self.report(code=f"error.{context}.node.category.missing", identifier=node_id)

        return biolink_class

    def validate_input_edge_node(self, context: str, node_id: Optional[str], category_name: Optional[str]):
        if node_id:
            category: Optional[ClassDefinition] = self.validate_category(
                context="input_edge",
                node_id=node_id,
                category=category_name
            )
            if category:
                # Since input edges are used in Query Graphs, we ought not to actually
                # care if they don't have at least one concrete category...However, it
                # is unlikely for non-concrete classes to resolve to a TRAPI response containing them!
                possible_subject_categories = self.bmt.get_element_by_prefix(node_id)
                if category.name not in possible_subject_categories:
                    self.report(
                        code="warning.input_edge.node.id.unmapped_to_category",
                        context=context,
                        identifier=node_id,
                        category=category_name
                    )
            else:
                self.report(
                    code="warning.input_edge.node.category.not_concrete",
                    identifier=node_id,
                    category=category_name
                )
        else:
            self.report(code="error.input_edge.node.id.missing", identifier=context)

    def check_biolink_model_compliance_of_input_edge(self, edge: Dict[str, str]):
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
        """
        # data fields to be validated...
        subject_category_curie = edge['subject_category'] if 'subject_category' in edge else None
        object_category_curie = edge['object_category'] if 'object_category' in edge else None
        predicate = edge['predicate'] if 'predicate' in edge else None
        subject_curie = edge['subject'] if 'subject' in edge else None
        object_curie = edge['object'] if 'object' in edge else None

        edge_id = f"{str(subject_curie)}--{predicate}->{str(object_curie)}"

        self.validate_input_edge_node(
            context='Subject',
            node_id=subject_curie,
            category_name=subject_category_curie
        )
        if not predicate:
            self.report(
                code="error.input_edge.predicate.missing",
                identifier=edge_id
            )
        else:
            self.validate_predicate(edge_id=edge_id, predicate=predicate)

        self.validate_input_edge_node(
            context='Object',
            node_id=object_curie,
            category_name=object_category_curie
        )

    def check_biolink_model_compliance(self, graph: Dict):
        """
        Validate a TRAPI-schema compliant Message graph-like data structure
        against the currently active Biolink Model Toolkit model version.

        :param graph: knowledge graph to be validated
        :type graph: Dict
        """
        if not graph:
            self.report(code="warning.graph.empty", identifier=self.graph_type.value)
            return  # nothing really more to do here!

        # Access graph data fields to be validated
        nodes: Optional[Dict]
        if 'nodes' in graph and graph['nodes']:
            nodes = graph['nodes']
        else:
            # Query Graphs can have an empty nodes catalog
            if self.graph_type is not TRAPIGraphType.Query_Graph:
                self.report(code="error.knowledge_graph.nodes.empty")
            # else:  Query Graphs can omit the 'nodes' tag
            nodes = None

        edges: Optional[Dict]
        if 'edges' in graph and graph['edges']:
            edges = graph['edges']
        else:
            if self.graph_type is not TRAPIGraphType.Query_Graph:
                self.report(code="error.knowledge_graph.edges.empty")
            # else:  Query Graphs can omit the 'edges' tag
            edges = None

        if nodes:
            for node_id, details in nodes.items():
                self.validate_graph_node(node_id, details)

            # Needed for the subsequent edge validation
            self.set_nodes(set(nodes.keys()))

            if edges:
                for edge in edges.values():
                    # print(f"{str(edge)}", flush=True)
                    self.validate_graph_edge(edge)


def check_biolink_model_compliance_of_input_edge(
        edge: Dict[str, str],
        biolink_version: Optional[str] = None,
        strict_validation: Optional[bool] = None
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
                            validated (Default: if None, use the Biolink Model Toolkit default version).
    :type biolink_version: Optional[str] = None
    :param strict_validation: if True, abstract and mixin elements validate as 'error'; False, issue 'info' message.
    :type strict_validation: bool = False

    :returns: Biolink Model validator cataloging validation messages (maybe empty)
    :rtype: BiolinkValidator
    """
    if strict_validation is None:
        # Test Input Edges are like Query Graph data,
        # hence, abstract and mixins ARE permitted
        strict_validation = False
    validator = BiolinkValidator(
        graph_type=TRAPIGraphType.Input_Edge,
        biolink_version=biolink_version,
        strict_validation=strict_validation
    )
    validator.check_biolink_model_compliance_of_input_edge(edge)
    return validator


def check_biolink_model_compliance_of_query_graph(
        graph: Dict,
        biolink_version: Optional[str] = None,
        strict_validation: Optional[bool] = None
) -> BiolinkValidator:
    """
    Validate a TRAPI-schema compliant Message Query Graph
    against a designated Biolink Model release.

    Since a Query graph is usually an incomplete knowledge graph specification,
    the validation undertaken is not 'strict'

    :param graph: query graph to be validated
    :type graph: Dict
    :param biolink_version: Biolink Model (SemVer) release against which the knowledge graph is to be
                            validated (Default: if None, use the Biolink Model Toolkit default version).
    :type biolink_version: Optional[str] = None
    :param strict_validation: if True, abstract and mixin elements validate as 'error'; False, issue 'info' message.
    :type strict_validation: Optional[bool] = None; defaults to 'False' if not set

    :returns: Biolink Model validator cataloging validation messages (maybe empty)
    :rtype: BiolinkValidator
    """
    # One typically won't be stringent in QueryGraph validation; however,
    # the strict_validation flag is set to a default of 'False' only if it is NOT set
    if strict_validation is None:
        # The default is that abstract and mixins are
        # allowed in Query Graphs for a TRAPI query
        strict_validation = False

    validator = BiolinkValidator(
        graph_type=TRAPIGraphType.Query_Graph,
        biolink_version=biolink_version,
        strict_validation=strict_validation
    )
    validator.check_biolink_model_compliance(graph)
    return validator


def  check_biolink_model_compliance_of_knowledge_graph(
    graph: Dict,
    trapi_version: Optional[str] = None,
    biolink_version: Optional[str] = None,
    sources: Optional[Dict] = None,
    strict_validation: Optional[bool] = None
) -> BiolinkValidator:
    """
    Strict validation of a TRAPI-schema compliant Message Knowledge Graph against a designated Biolink Model release.

    :param graph: knowledge graph to be validated.
    :type graph: Dict
    :param trapi_version: TRAPI schema (SemVer) release against which the knowledge graph is to be
                            validated (Default: if None, use the latest available version).
    :type trapi_version: Optional[str] = None
    :param biolink_version: Biolink Model (SemVer) release against which the knowledge graph is to be
                            validated (Default: if None, use the Biolink Model Toolkit default version).
    :type biolink_version: Optional[str] = None
    :param sources: Dictionary of validation context identifying the ARA and KP for provenance attribute validation
    :type sources: Dict
    :param strict_validation: if True, abstract and mixin elements validate as 'error'; False, issue 'info' message.
    :type strict_validation: Optional[bool] = None; defaults to 'True' if not set

    :returns: Biolink Model validator cataloging validation messages (maybe empty)
    :rtype: BiolinkValidator
    """
    # One typically will want stringent validation for Knowledge Graphs; however,
    # the strict_validation flag is set to a default of 'True' only if it is NOT set
    if strict_validation is None:
        # Knowledge Graphs generally ought NOT to use
        # abstract and mixins in TRAPI Responses (and Requests)
        strict_validation = True

    validator = BiolinkValidator(
        graph_type=TRAPIGraphType.Knowledge_Graph,
        trapi_version=trapi_version,
        biolink_version=biolink_version,
        sources=sources,
        strict_validation=strict_validation
    )
    validator.check_biolink_model_compliance(graph)
    return validator
