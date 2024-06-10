"""
Version-specific Biolink Model semantic validation of knowledge graph components.
"""
from typing import Optional, Any, Dict, List, Tuple
from numbers import Number
from functools import lru_cache
import re
from urllib.error import HTTPError
from pprint import PrettyPrinter


from bmt import Toolkit, utils
from linkml_runtime.linkml_model import ClassDefinition, Element

from reasoner_validator.versioning import SemVer, SemVerError
from reasoner_validator.message import MESSAGES_BY_TARGET
from reasoner_validator.trapi import TRAPISchemaValidator
from reasoner_validator.report import TRAPIGraphType

import logging
logger = logging.getLogger(__name__)

pp = PrettyPrinter(indent=4)


CURIE_PATTERN = re.compile(r"^[^ <()>:]*:[^/ :]+$")


def is_curie(s: str) -> bool:
    """
    Check if a given string is a CURIE.

    :param s: str, string to be validated as a CURIE
    :return: bool, whether the given string is a CURIE
    """
    # Method copied from kgx.prefix_manager.PrefixManager...
    if isinstance(s, str):
        m = CURIE_PATTERN.match(s)
        return bool(m)
    else:
        return False


def get_reference(curie: str) -> Optional[str]:
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
    if is_curie(curie):
        reference = curie.split(":", 1)[1]
    return reference


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


class BMTWrapper:
    def __init__(self, biolink_version: Optional[str] = None):
        self.bmt: Optional[Toolkit] = None
        self.default_biolink: bool = False
        if biolink_version != "suppress":
            # Here, the Biolink Model version is validated, and the relevant Toolkit pulled.
            if biolink_version is None:
                self.default_biolink = True
            self.bmt = get_biolink_model_toolkit(biolink_version=biolink_version)
            self.biolink_version = self.bmt.get_model_version()
        else:
            self.biolink_version = "suppress"

        logger.debug(f"Resolved Biolink Model Version: '{self.biolink_version}'")

    def get_biolink_version(self) -> str:
        """
        :return: Biolink Model version currently targeted by the ValidationReporter.
        :rtype biolink_version: str
        """
        return self.biolink_version

    def reset_biolink_version(self, version: str):
        """
        Reset Biolink Model version tracked by the ValidationReporter.
        :param version: new version
        :return: None
        """
        self.biolink_version = version

    def get_bmt(self) -> Optional[Toolkit]:
        return self.bmt

    def is_symmetric(self, name: str) -> bool:
        """
        Checks if a given element identified by name, is a symmetric (predicate) slot.
        :param name: name of the element
        :return: True if element is a symmetric (predicate) slot.
        """
        # TODO: perhaps this method ought to be in the Biolink Model Toolkit?
        if not name:
            return False
        element: Optional[Element] = self.bmt.get_element(name)
        if element is not None and element['symmetric']:
            return True
        else:
            return False

    def get_inverse_predicate(self, predicate: Optional[str]) -> Optional[str]:
        """
        Utility wrapper of logic to robustly test if a predicate exists and has an inverse.
        :param predicate: CURIE or string name of predicate for which the inverse is sought.
        :return: CURIE string of inverse predicate, if it exists; None otherwise
        """
        # TODO: perhaps this method ought to be in the Biolink Model Toolkit?
        if predicate and self.bmt.is_predicate(predicate):
            predicate_name = utils.parse_name(predicate)
            inverse_predicate_name = self.bmt.get_inverse(predicate_name)
            if not inverse_predicate_name:
                if self.is_symmetric(predicate_name):
                    inverse_predicate_name = predicate_name
                else:
                    inverse_predicate_name = None

            if inverse_predicate_name:
                ip = self.bmt.get_element(inverse_predicate_name)
                return utils.format_element(ip)
        return None


class BiolinkValidator(TRAPISchemaValidator, BMTWrapper):
    """
    Wrapper class for Biolink Model validation of a TRAPI message.
    """
    def __init__(
        self,
        default_test: Optional[str] = None,
        default_target: Optional[str] = None,
        trapi_version: Optional[str] = None,
        biolink_version: Optional[str] = None,
        target_provenance: Optional[Dict[str, str]] = None,
        strict_validation: Optional[bool] = None
    ):
        """
        Biolink Validator constructor.
        :param default_test: Optional[str] =  None, initial default test context of the BiolinkValidator messages
        :param default_target: Optional[str] =  None, initial default target context of the BiolinkValidator,
                                                also used as a prefix in validation messages.
        :param trapi_version:  Optional[str], caller specified Biolink Model version (default: None, use TRAPI 'latest')
        :param biolink_version: Optional[str], caller specified Biolink Model version (default: None, use BMT 'latest')
                                Note that a special biolink_version value string "suppress" disables full Biolink Model
                                validation by the validator (i.e. limits validation to superficial validation).
        :param target_provenance: Optional[Dict[str,str]], Dictionary of context ARA and KP for provenance validation
        :param strict_validation: Optional[bool] = None, if True, some tests validate as 'error';  False, simply issues
                                  'info' message; A value of 'None' uses the default value for specific graph contexts.

        """
        BMTWrapper.__init__(self, biolink_version=biolink_version)
        TRAPISchemaValidator.__init__(
            self,
            default_test=default_test,
            default_target=default_target if default_target else f"Biolink Validation",
            trapi_version=trapi_version,
            strict_validation=strict_validation
        )
        self.target_provenance: Optional[Dict] = target_provenance

        # the internal 'nodes' dictionary, indexed by 'node_id' key, tracks
        # the associated Biolink Model node categories, plus a usage count for the node_id key
        self.nodes: Dict[str, List[Optional[List[str]], int]] = dict()

        # predicate flag assessing completeness of individual TRAPI Responses
        self._has_valid_qnode_information: bool = False

    def get_biolink_version(self) -> str:
        """
        :return: Biolink Model version currently tracked by the TRAPISchemaValidator.
        :rtype biolink_version: str
        """
        return BMTWrapper.get_biolink_version(self)

    def reset_biolink_version(self, version: str):
        """
        Reset Biolink Model version tracked by the ValidationReporter.
        :param version: new version
        :return: None
        """
        BMTWrapper.reset_biolink_version(self, version)

    def validate_biolink(self) -> bool:
        """
        Predicate to check if the Biolink (version) is
        tagged to 'suppress' compliance validation.

        :return: bool, returns 'True' if Biolink Validation is expected.
        """
        return self.biolink_version is not None and self.biolink_version.lower() != "suppress"

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

    def reset_node_info(self, graph_type: TRAPIGraphType):
        if graph_type == TRAPIGraphType.Query_Graph:
            self._has_valid_qnode_information: bool = False

    def has_valid_node_information(self, graph_type: TRAPIGraphType) -> bool:
        if graph_type == TRAPIGraphType.Query_Graph:
            return self._has_valid_qnode_information
        else:
            # Not relevant or dealt with elsewhere for other graph types
            return True

    def count_node(self, node_id: str):
        self.nodes[node_id][1] += 1

    def has_dangling_nodes(self) -> List[str]:
        return [node_id for node_id, entry in self.nodes.items() if not entry[1]]

    def get_result(self) -> Tuple[str, MESSAGES_BY_TARGET]:
        """
        Get result of validation.

        :return: model version of the validation and dictionary of reported validation messages.
        :rtype Tuple[str, Optional[Dict[str, Set[str]]]]
        """
        return self.bmt.get_model_version(), super().get_all_messages()

    def validate_graph_node(self, node_id: str, slots: Dict[str, Any], graph_type: TRAPIGraphType):
        """
        Validate slot properties (mainly 'categories') of a node.

        :param node_id: str, identifier of a concept node
        :param slots: Dict, properties of the node
        :param graph_type: TRAPIGraphType, properties of the node
        """
        logger.debug(f"{node_id}: {str(slots)}")

        if graph_type is TRAPIGraphType.Knowledge_Graph:
            if self.validate_biolink():
                # This will fail for an earlier TRAPI data schema version
                # which didn't use the tag 'categories' for nodes...
                # But this earlier TRAPI release is no longer relevant to the community?
                if 'categories' in slots:
                    if not isinstance(slots["categories"], List):
                        self.report(code="error.knowledge_graph.node.categories.not_array", identifier=node_id)
                    else:
                        # Biolink Validation of node, if not suppressed
                        categories = slots["categories"]
                        node_prefix_mapped: bool = False
                        concrete_category_found: bool = False
                        included_category: Optional[str] = None
                        for category in categories:
                            concrete_category: Optional[ClassDefinition] = \
                                self.validate_category(
                                    context="knowledge_graph",
                                    node_id=node_id,
                                    category=category
                                )
                            # Only 'concrete' (non-abstract, non-mixin, preferably,
                            # non-deprecated) categories are of interest here,
                            # since only they will have associated namespaces
                            if concrete_category:
                                concrete_category_found: bool = True
                                possible_subject_categories = self.bmt.get_element_by_prefix(node_id)
                                if possible_subject_categories and \
                                        concrete_category.name in possible_subject_categories:
                                    node_prefix_mapped = True
                                    # don't need to search any more categories
                                    break
                            else:
                                # See above note about CATEGORY_INCLUSIONS
                                if category in self.CATEGORY_INCLUSIONS:
                                    included_category = category

                        if not concrete_category_found:
                            # Although we didn't find any concrete categories, maybe
                            # we instead saw one of the 'included' abstract/mixin categories
                            if included_category is not None:
                                self.report(
                                    code=f"warning.knowledge_graph.node.category.abstract_or_mixin",
                                    identifier=concrete_category_found,
                                    node_id=node_id
                                )
                            else:
                                self.report(
                                    code="error.knowledge_graph.node.categories.not_concrete",
                                    identifier=node_id,
                                    categories=str(categories)
                                )

                        if not node_prefix_mapped:
                            self.report(
                                code="warning.knowledge_graph.node.id.unmapped_prefix",
                                identifier=str(categories),
                                node_id=node_id
                            )
                else:
                    self.report(
                        code="error.knowledge_graph.node.category.missing",
                        identifier=node_id
                    )

                # UI team request (part of issue #35): really need names here
                if not ("name" in slots and slots["name"]):
                    self.report(
                        code="warning.knowledge_graph.node.name.missing",
                        identifier=node_id
                    )

                # TODO: Do we need to (or can we) validate here, any other
                #       Knowledge Graph node fields? Perhaps not yet?

        else:  # Query Graph node validation

            has_node_ids: bool = False
            node_ids: List[str] = list()
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

            has_categories: bool = False
            if "categories" in slots:
                categories = slots["categories"]
                if categories:
                    if not isinstance(categories, List):
                        self.report(code="error.query_graph.node.categories.not_array", identifier=node_id)
                    else:
                        has_categories = True  # assume that we have some categories, even if ill-formed
                        if self.validate_biolink():
                            # Biolink Validation of node, if not suppressed
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

                            # At this point, if any 'node_ids' are NOT
                            # removed (above), then they are unmapped
                            if has_node_ids and not all([mapped for mapped in id_prefix_mapped.values()]):
                                self.report(
                                    code="warning.query_graph.node.ids.unmapped_prefix",
                                    identifier=node_id,
                                    unmapped_ids=str(node_ids),
                                    categories=str(categories)
                                )

                # else:  # null "categories" value is permitted in QNodes by nullable: true, has_categories == False
            # else:  # missing "categories" key is permitted in QNodes by nullable: true, has_categories == False

            if 'is_set' in slots:
                is_set = slots["is_set"]
                if is_set and not isinstance(is_set, bool):
                    self.report(code="error.query_graph.node.is_set.not_boolean", identifier=node_id)
            # else:  # a missing key or null "is_set" value is permitted in QNodes but defaults to 'False'

            # constraints  # TODO: how do we validate node constraints?

            # Here we record whether we encountered at least
            # one informative node in the Query Graph
            if has_node_ids or has_categories:
                self._has_valid_qnode_information = True

    def set_nodes(self, nodes: Dict):
        """
        Records additional nodes, uniquely by node_id, with specified categories.
        :param nodes: Dict, node_id indexed node categories. A given node_id is
        tagged with "None" if the categories are missing?
        :return: None
        """
        self.nodes.update(
            {
                # We don't now bother to set the categories, if not provided
                node_id: [details['categories'] if 'categories' in details and details['categories'] else None, 0]
                for node_id, details in nodes.items()
            }
        )

    def get_node_identifiers(self) -> List[str]:
        """
        :return: List of currently registered node_ids
        """
        return list(self.nodes.keys())

    def get_node_categories(self, node_id: str) -> Optional[List[str]]:
        """
        Categories by 'node_id'.
        :param node_id:
        :return: For a given node_id, returns the associated categories;
                 None if node_id is currently unknown or has no categories.
        """
        return self.nodes[node_id][0] if node_id in self.nodes else None

    def validate_element_status(
            self,
            graph_type: TRAPIGraphType,
            context: str,
            identifier: str,
            edge_id: str,
            source_trail: Optional[str] = None,
            ignore_graph_type: bool = False
    ) -> Optional[Element]:
        """
        Detect element missing from Biolink, or is deprecated, abstract or mixin, signalled as a failure or warning.

        :param graph_type: TRAPIGraphType, type of TRAPI graph component being validated
        :param context: str, parsing context (e.g. 'Node')
        :param identifier: str, name of the putative Biolink element ('class')
        :param edge_id: str, identifier of enclosing edge containing the element (e.g. the 'edge_id')
        :param source_trail: Optional[str], audit trail of knowledge source provenance for a given Edge, as a string.
        :param ignore_graph_type: bool, if strict validation is None (not set globally), then
               only apply graph-type-differential strict validation if 'ignore_graph_type' is False
        :return: Optional[Element], Biolink Element resolved to 'name' if element no validation error; None otherwise.
        """
        element: Optional[Element] = self.bmt.get_element(identifier)
        if not element:
            self.report(
                code=f"error.{context}.unknown",
                source_trail=source_trail,
                identifier=identifier,
                edge_id=edge_id
            )
            return None

        if element.deprecated:
            # We won't index the instances where the deprecated element is seen, since we assume that
            # component developers learning about the issue will globally fix it in their graphs
            self.report(
                code=f"warning.{context}.deprecated",
                source_trail=source_trail,
                identifier=identifier
            )
            # return None - a deprecated term is not treated as a failure but just as a warning

        if element.abstract:
            if self.is_strict_validation(graph_type):
                self.report(
                    code=f"error.{context}.abstract",
                    source_trail=source_trail,
                    identifier=identifier,
                    edge_id=edge_id
                )
                return None
            else:
                self.report(
                    code=f"info.{context}.abstract",
                    source_trail=source_trail,
                    identifier=identifier,
                    edge_id=edge_id
                )

        elif self.bmt.is_mixin(identifier):
            # A mixin cannot be instantiated ...
            # but can be used in QueryGraphs
            # or when explicitly permitted
            if self.is_strict_validation(graph_type, ignore_graph_type=ignore_graph_type):
                self.report(
                    code=f"error.{context}.mixin",
                    source_trail=source_trail,
                    identifier=identifier,
                    edge_id=edge_id
                )
                return None
            else:
                self.report(
                    code=f"info.{context}.mixin",
                    source_trail=source_trail,
                    identifier=identifier,
                    edge_id=edge_id
                )

        return element

    def get_target_provenance(self) -> Tuple[Optional[str], Optional[str], Optional[str]]:
        """
        Returns infores-prefix-normalized target provenance metadata.
        :return: Tuple[Optional[str], Optional[str], Optional[str]] of ara_source, kp_source, kp_source_type
        """
        ara_source: Optional[str] = None
        kp_source: Optional[str] = None
        kp_source_type: Optional[str] = None
        if self.target_provenance:
            if 'ara_source' in self.target_provenance and self.target_provenance['ara_source']:
                ara_source: str = self.target_provenance['ara_source']
                if not ara_source.startswith("infores:"):
                    ara_source = f"infores:{ara_source}"
            if 'kp_source' in self.target_provenance and self.target_provenance['kp_source']:
                kp_source: str = self.target_provenance['kp_source']
                if not kp_source.startswith("infores:"):
                    kp_source = f"infores:{kp_source}"
            kp_source_type = self.target_provenance['kp_source_type'] \
                if 'kp_source_type' in self.target_provenance and self.target_provenance['kp_source_type'] \
                else 'aggregator'
            kp_source_type = f"biolink:{kp_source_type}_knowledge_source"

        return ara_source, kp_source, kp_source_type

    def validate_provenance(
            self,
            edge_id,
            ara_source, found_ara_knowledge_source,
            kp_source, found_kp_knowledge_source, kp_source_type,
            found_primary_knowledge_source,
            source_trail: Optional[str]
    ):
        """
        Validates ARA and KP infores knowledge sources based on surveyed Edge slots
        (recorded in edge "attributes" pre-1.4.0; in "sources", post-1.4.0).

        :param edge_id: str, string identifier for the edge (for reporting purposes)
        :param ara_source: str, user specified target ARA infores
        :param found_ara_knowledge_source: bool, True if target ARA infores knowledge source was found
        :param kp_source: str, user specified target KP infores
        :param found_kp_knowledge_source:  bool, True if target KP infores knowledge source was found
        :param kp_source_type:  str, user specified KP knowledge source type (i.e. primary, aggregate, etc.)
        :param source_trail: Optional[str], audit trail of knowledge source provenance for a given Edge, as a string.
        :param found_primary_knowledge_source: List[str], list of all infores discovered tagged as 'primary'
        :return:
        """
        if ara_source and not found_ara_knowledge_source:
            # found target ARA knowledge source (if applicable)
            self.report(
                code="warning.knowledge_graph.edge.provenance.ara.missing",
                source_trail=source_trail,
                identifier=ara_source,
                edge_id=edge_id
            )

        if kp_source and not found_kp_knowledge_source:
            # found target KP knowledge source (if applicable)
            self.report(
                code="warning.knowledge_graph.edge.provenance.kp.missing",
                source_trail=source_trail,
                identifier=kp_source,
                kp_source_type=kp_source_type,
                edge_id=edge_id
            )

        if not found_primary_knowledge_source:
            # Found a primary tagged source...
            self.report(
                code="error.knowledge_graph.edge.provenance.missing_primary",
                source_trail=source_trail,
                identifier=edge_id
            )
        elif len(found_primary_knowledge_source) > 1:
            # ... but only one!
            self.report(
                code="warning.knowledge_graph.edge.provenance.multiple_primary",
                source_trail=source_trail,
                identifier=edge_id,
                sources=",".join(found_primary_knowledge_source)
            )

    def validate_slot_value(
            self,
            slot_name: str,
            context: str,
            found: bool,
            value: Optional[str]
    ) -> bool:
        """
        Validate the single-valued value of a specified slot of the given knowledge graph entity slot.
        :param slot_name, str, name of a valid slot, a value for which is to be validated
        :param context: str, context of the validation (e.g. node or edge id)
        :param found: bool, current status of slot detection,
                      Should be true if the slot was already previously seen
        :param value: Optional[str], the value to be validated
        :return: bool, True if valid slot and value (validation messages recorded in the BiolinkValidator)
        """
        if found:
            # The slot was already encountered in this element,
            # hence report the duplication with its value?
            self.report(
                code=f"error.knowledge_graph.edge.{slot_name}.duplicated",
                identifier=context,
                value=str(value)
            )
            # we'll be forgiving here and just assume
            # that the first slot value was acceptable.
            return True

        slot_element = self.bmt.get_element(f"biolink:{slot_name}")
        assert slot_element, f"No such slot {slot_name} element in Biolink Model release {self.biolink_version}"

        # Note: we don't need to check for empty attribute.values
        # here since done elsewhere in the code base

        # Validate slot value here against the specified slot range Enum
        if "range" in slot_element and slot_element.range:
            value_range = slot_element.range
            if value_range and self.bmt.is_enum(value_range):
                enum = self.bmt.view.get_enum(value_range)
                if not self.bmt.is_permissible_value_of_enum(enum.name, value):
                    self.report(
                        code=f"error.knowledge_graph.edge.{slot_name}.invalid",
                        identifier=str(value),
                        context=context
                    )
                    return False
                else:
                    # if this passes all the gauntlets, assert
                    # that the slot and its value were found
                    return True

        # Catch this as a warning against a missing
        # Biolink Model element range specification
        self.report(
            code=f"warning.biolink.element.range.unspecified",
            identifier=slot_name,
            context=context,
            value=str(value)
        )
        return False

    def validate_knowledge_level(
            self,
            edge_id: str,
            found: bool,
            value: Optional[str]
    ) -> bool:
        """
        Validate the value of a 'knowledge_level' of the given edge.
        :param edge_id: str, identifier of the edge being validated
        :param found: bool, current status of slot detection, True if already seen previously (return 'True' value here)
        :param value: Optional[str], the value to be validated
        :return: bool, if valid slot and value found (validation messages recorded in the BiolinkValidator)
        """
        return self.validate_slot_value(slot_name="knowledge_level", context=edge_id, found=found, value=value)

    def validate_agent_type(
            self,
            edge_id: str,
            found: bool,
            value: Optional[str]
    ) -> bool:
        """
        Validate the value of a 'agent_type' of the given edge.
        :param edge_id: str, identifier of the edge being validated
        :param found: bool, current status of slot detection, True if already seen previously (return 'True' value here)
        :param value: Optional[str], the value to be validated
        :return: None (validation messages recorded in the BiolinkValidator)
        """
        return self.validate_slot_value(slot_name="agent_type", context=edge_id, found=found, value=value)

    def get_attribute_type_exclusions(self) -> List[str]:
        if self.minimum_required_biolink_version("4.2.0"):
            return list()
        else:
            # 13-July-2023: Certain attribute_type_id's are slated for future implementation in the Biolink Model
            #               but not in the current model release; however, some teams have started to use the terms.
            #               We therefore put them on a special "inclusion list" (like the CATEGORY_INCLUSIONS below)
            #               to permit them to pass through the validation without any complaints.
            # Still not defined in Biolink releases prior to "4.2.0'
            # but sometimes implemented: ignore in validation
            return ["biolink:knowledge_level", "biolink:agent_type"]

    def validate_attributes(
            self,
            graph_type: TRAPIGraphType,
            edge_id: str,
            edge: Dict,
            source_trail: Optional[str] = None
    ) -> Optional[str]:
        """
        Validate Knowledge Edge Attributes. For TRAPI 1.3.0, may also return an ordered audit trail of Edge provenance
        infores-specified knowledge sources, as parsed in from the list of attributes (returns 'None' otherwise).

        :param graph_type: TRAPIGraphType, type of TRAPI graph component being validated
        :param edge_id: str, string identifier for the edge (for reporting purposes)
        :param edge: Dict, the edge object associated with some attributes are expected to be found
        :param source_trail: Optional[str], audit trail of knowledge source provenance for a given Edge, as a string.
        :return: Optional[str], audit trail of knowledge source provenance for a given Edge, as a string.
        """
        # in TRAPI 1.4.0, the source_trail is parsed in from the Edge.sources annotation, hence
        # the source_trail is already known and given to this method for reporting purposes here

        # Otherwise, in TRAPI 1.3.0, the 'sources' may be compiled here, in this method, from the attributes
        # themselves, then a newly generated 'source_trail', returned for use by the rest of the application
        # sources: Dict[str, List[str]] = dict()

        # we only report errors about missing or empty edge attributes if TRAPI 1.3.0 or earlier,
        # and Biolink Validation is not suppressed, since we can't fully validate provenance and
        # since earlier TRAPI releases are minimally expected to record provenance attributes
        # we only report this for TRAPI < 1.4 when Biolink Validation is done given that
        # without Biolink validation, provenance cannot be reliably assessed

        # We can already use 'source_trail' here in the report in case it was
        # already pre-computed by the validate_sources parsing of TRAPI 1.4.0;
        # if TRAPI 1.3.0 is the validation standard, the 'source_trail' would
        # be undefined here, since we can't figure it out without attributes!
        if 'attributes' not in edge:
            if self.validate_biolink() and not self.minimum_required_trapi_version("1.4.0-beta"):
                # Note: Only an error for earlier TRAPI versions
                # since attributes are 'nullable: True' for TRAPI 1.4.0
                self.report(
                    code="error.knowledge_graph.edge.attribute.missing",
                    identifier=edge_id,
                    source_trail=source_trail
                )
        elif not edge['attributes']:
            if self.validate_biolink() and not self.minimum_required_trapi_version("1.4.0-beta"):
                # Note: Only an error for earlier TRAPI versions
                # since attributes are 'nullable: True' for TRAPI 1.4.0
                self.report(
                    code="error.knowledge_graph.edge.attribute.empty",
                    identifier=edge_id,
                    source_trail=source_trail
                )
        elif not isinstance(edge['attributes'], List):
            self.report(
                code="error.knowledge_graph.edge.attribute.not_array",
                identifier=edge_id,
                source_trail=source_trail
            )
        else:
            attributes = edge['attributes']

            # EDeutsch feedback: maybe we don't need to capture TRAPI 1.3.0 attribute-defined 'sources'
            # raise NotImplementedError("Implement capture of 'sources' from TRAPI 1.3.0 attributes!")
            # source_trail = self.build_source_trail(sources) if sources else None

            ara_source: Optional[str]
            kp_source: Optional[str]
            kp_source_type: Optional[str]
            ara_source, kp_source, kp_source_type = self.get_target_provenance()

            # Expecting ARA and KP 'aggregator_knowledge_source' attributes?
            found_ara_knowledge_source = False
            found_kp_knowledge_source = False

            # also track primary_knowledge_source attribute cardinality now
            found_primary_knowledge_source: List[str] = list()

            # Track presence of 'knowledge_level' and 'agent_type' attributes
            found_knowledge_level = False
            found_agent_type = False

            # TODO: Defer tracking of the presence of 'biolink:support_graphs'
            #       for specified predicates like 'treats' or its descendants
            # found_support_graphs = False

            for attribute in attributes:

                # Validate attribute_type_id
                if 'attribute_type_id' not in attribute:
                    self.report(
                        code="error.knowledge_graph.edge.attribute.type_id.missing",
                        identifier=edge_id,
                        source_trail=source_trail
                    )
                elif not attribute['attribute_type_id']:
                    self.report(
                        code="error.knowledge_graph.edge.attribute.type_id.empty",
                        identifier=edge_id,
                        source_trail=source_trail
                    )
                else:
                    attribute_type_id: str = attribute['attribute_type_id']
                    if 'value' not in attribute:
                        self.report(
                            code="error.knowledge_graph.edge.attribute.value.missing",
                            identifier=edge_id,
                            attribute_id=attribute_type_id,
                            source_trail=source_trail
                        )
                    else:
                        value = attribute['value']
                        if isinstance(value, bool) or isinstance(value, Number):
                            # An attribute value which is a Python bool of value 'False'
                            # or a numeric value with value zero, is acceptable...
                            pass

                        # ...But not other datatype values deemed 'empty'
                        elif not value or \
                                str(value).upper() in ["N/A", "NONE", "NULL"]:
                            self.report(
                                code="error.knowledge_graph.edge.attribute.value.empty",
                                identifier=edge_id,
                                attribute_id=attribute_type_id,
                                source_trail=source_trail
                            )
                        else:
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
                                    edge_id=edge_id,
                                    source_trail=source_trail
                                )
                            elif self.validate_biolink():
                                # 'attribute_type_id' is a CURIE, but how well does it map?
                                prefix = attribute_type_id.split(":", 1)[0]
                                if prefix == 'biolink':
                                    # We will skip further validation of terms
                                    # in the ATTRIBUTE_TYPE_ID_INCLUSIONS list...
                                    if attribute_type_id not in self.get_attribute_type_exclusions():

                                        # ... but further validate everything else...
                                        biolink_class = self.validate_element_status(
                                            graph_type=graph_type,
                                            context="knowledge_graph.edge.attribute.type_id",
                                            identifier=attribute_type_id,
                                            edge_id=edge_id,
                                            source_trail=source_trail
                                        )
                                        if biolink_class:
                                            if self.bmt.is_category(name=biolink_class.name):
                                                self.report(
                                                    code="warning.knowledge_graph.edge.attribute.type_id.is_category",
                                                    identifier=attribute_type_id,
                                                    edge_id=edge_id,
                                                    source_trail=source_trail
                                                )
                                            elif self.bmt.is_predicate(name=biolink_class.name):
                                                self.report(
                                                    code="warning.knowledge_graph.edge.attribute.type_id.is_predicate",
                                                    identifier=attribute_type_id,
                                                    edge_id=edge_id,
                                                    source_trail=source_trail
                                                )
                                            elif not self.bmt.is_association_slot(attribute_type_id):
                                                self.report(
                                                    code="warning.knowledge_graph.edge." +
                                                         "attribute.type_id.not_association_slot",
                                                    identifier=attribute_type_id,
                                                    edge_id=edge_id,
                                                    source_trail=source_trail
                                                )
                                            else:
                                                # attribute_type_id is a Biolink 'association_slot': validate further...

                                                # TODO: only check knowledge_source provenance here for now. Are there
                                                #       other association_slots to be validated here too? For example,
                                                #       once new terms with defined value ranges are published in the
                                                #       Biolink Model, then perhaps 'value' validation will be feasible.

                                                # Edge provenance tags only recorded in
                                                # Edge attributes prior to TRAPI 1.4.0-beta
                                                if not self.minimum_required_trapi_version("1.4.0-beta"):

                                                    if attribute_type_id in \
                                                            [
                                                                "biolink:aggregator_knowledge_source",
                                                                "biolink:primary_knowledge_source",

                                                                # Note: deprecated since Biolink release 3.0.2
                                                                #       but this is probably caught above in the
                                                                #       'validate_element_status' method predicate
                                                                "biolink:original_knowledge_source"
                                                            ]:

                                                        # ... now, check the infores values against various expectations
                                                        for infores in value:
                                                            if not infores.startswith("infores:"):
                                                                self.report(
                                                                   code="error.knowledge_graph.edge." +
                                                                        "provenance.infores.missing",
                                                                   identifier=str(infores),
                                                                   edge_id=edge_id,
                                                                   source_trail=source_trail
                                                                )
                                                            else:
                                                                if attribute_type_id == \
                                                                        "biolink:primary_knowledge_source":
                                                                    found_primary_knowledge_source.append(infores)

                                                                if ara_source and \
                                                                   attribute_type_id == \
                                                                        "biolink:aggregator_knowledge_source" \
                                                                        and infores == ara_source:
                                                                    found_ara_knowledge_source = True
                                                                elif kp_source and \
                                                                        attribute_type_id == kp_source_type and \
                                                                        infores == kp_source:
                                                                    found_kp_knowledge_source = True

                                                # TODO: Defer tracking of the presence of 'biolink:support_graphs'
                                                #       for specified predicates like 'treats' or its descendants
                                                # if attribute_type_id == "biolink:support_graphs":
                                                #     found_support_graphs = False

                                                # We expect at this point that, if 'attribute_type_id' is a
                                                # 'knowledge_level' or 'agent_type', then the value is a scalar
                                                value = value[0]

                                                # We won't likely care if 'knowledge_level' or 'agent_type'
                                                # show up in graphs compliant with Biolink earlier than 4.2.0,
                                                # but we validate their values anyhow...
                                                if attribute_type_id == "biolink:knowledge_level":
                                                    found_knowledge_level = \
                                                        self.validate_knowledge_level(
                                                            edge_id=edge_id,
                                                            found=found_knowledge_level,
                                                            value=value
                                                        )
                                                elif attribute_type_id == "biolink:agent_type":
                                                    found_agent_type = \
                                                        self.validate_agent_type(
                                                            edge_id=edge_id,
                                                            found=found_agent_type,
                                                            value=value
                                                        )

                                # if not a Biolink model defined attribute term, at least, check if
                                # the 'attribute_type_id' has a namespace (prefix) known to Biolink.
                                # We won't call it a hard error, but issue a warning
                                elif not self.bmt.get_element_by_prefix(attribute_type_id):
                                    self.report(
                                        code="warning.knowledge_graph.edge." +
                                             "attribute.type_id.non_biolink_prefix",
                                        identifier=attribute_type_id,
                                        edge_id=edge_id,
                                        source_trail=source_trail
                                    )

            # Edge provenance tags only recorded in Edge attributes prior to TRAPI 1.4.0-beta
            if not self.minimum_required_trapi_version("1.4.0-beta") and self.validate_biolink():
                # After all the attributes have been scanned,
                # check for provenance. Treat as warnings for now.
                # Note that provenance checking is only done when Biolink validation is done
                # (since the various flags are not properly set above, for the test)
                self.validate_provenance(
                    edge_id,
                    ara_source, found_ara_knowledge_source,
                    kp_source, found_kp_knowledge_source, kp_source_type,
                    found_primary_knowledge_source,
                    source_trail=source_trail
                )

            # Mandatory 'knowledge_level' and 'agent_type'
            # attributes required in all Biolink Model edges
            # from Biolink Model release 4.2.0 onwards
            if self.minimum_required_biolink_version("4.2.0"):
                if not found_knowledge_level:
                    # Currently projected to be mandatory only in TRAPI 1.6.0
                    if self.minimum_required_trapi_version("1.6.0"):
                        self.report(
                            code="error.knowledge_graph.edge.knowledge_level.missing",
                            identifier=edge_id
                        )
                    else:
                        self.report(
                            code="warning.knowledge_graph.edge.knowledge_level.missing",
                            identifier=edge_id
                        )

                if not found_agent_type:
                    # Currently projected to be mandatory only in TRAPI 1.6.0
                    if self.minimum_required_trapi_version("1.6.0"):
                        self.report(
                            code="error.knowledge_graph.edge.agent_type.missing",
                            identifier=edge_id
                        )
                    else:
                        self.report(
                            code="warning.knowledge_graph.edge.agent_type.missing",
                            identifier=edge_id
                        )

                # TODO: Defer tracking of the presence of 'biolink:support_graphs'
                #       for specified predicates like 'treats' or its descendants
                # predicate = edge['predicate'] if 'predicate' in edge else None
                # if self.is_treats(predicate) and not found_support_graphs:
                #     self.report(
                #         code="warning.knowledge_graph.edge.treats.support_graph.missing",
                #         identifier=edge_id
                #     )

        return source_trail  # may be 'None' if the required attributes are missing

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
            # attribute_constraints: List = edge['attribute_constraints']
            pass

    def validate_qualifier_entry(
            self,
            context: str,
            edge_id: str,
            qualifiers: List[Dict[str, str]],
            associations: Optional[List[str]] = None,
            source_trail: Optional[str] = None
    ):
        """
        Validate Qualifier Entry (JSON Object).

        :param context: str, Validation (subcode) context:
                        - query graph qualifier constraints ("query_graph.edge.qualifier_constraints.qualifier_set") or
                        - knowledge graph edge qualifiers (knowledge_graph.edge.qualifiers)
        :param edge_id: str, string identifier for the edge (for reporting purposes)
        :param qualifiers: List[Dict[str, str]], of qualifier entries to be validated.
        :param associations: Optional[List[str]] = None,
                             Biolink association subclasses possibly related to the current edge.
        :param source_trail, Optional[str], audit trail of knowledge source provenance for a given Edge, as a string.
                             Defaults to "global" if not specified.
        :return: None (validation messages captured in the 'self' BiolinkValidator context)
        """
        for qualifier in qualifiers:
            qualifier_type_id: str = qualifier['qualifier_type_id']
            qualifier_value: str = qualifier['qualifier_value']
            try:
                if not self.bmt.is_qualifier(name=qualifier_type_id):
                    self.report(
                        code=f"error.{context}.qualifier.type_id.unknown",
                        source_trail=source_trail,
                        identifier=qualifier_type_id,
                        edge_id=edge_id
                    )
                elif qualifier_type_id == "biolink:qualified_predicate":
                    if not self.bmt.is_predicate(qualifier_value):
                        # special case of qualifier must have Biolink predicates as values
                        self.report(
                            code=f"error.{context}.qualifier.value.not_a_predicate",
                            source_trail=source_trail,
                            identifier=qualifier_value,
                            edge_id=edge_id
                        )

                # A Query Graph miss on qualifier_value is less an issue since there may not be enough
                # context to resolve the 'qualifier_value'; whereas a Knowledge Graph miss is more severe
                elif context.startswith("knowledge_graph") and \
                        not self.bmt.validate_qualifier(
                            qualifier_type_id=qualifier_type_id,
                            qualifier_value=qualifier_value,
                            associations=associations
                        ):
                    # TODO: to review (as of release  3.8.9) we demoted this validation message to a 'warning',
                    #       since in most components (Sept 2023), the KP asserted qualifier values are likely
                    #       reasonable, but the qualifier value curation of the Biolink Model is as yet incomplete
                    self.report(
                        code=f"warning.{context}.qualifier.value.unresolved",
                        source_trail=source_trail,
                        identifier=qualifier_value,
                        edge_id=edge_id,
                        qualifier_type_id=qualifier_type_id
                    )
            except Exception as e:
                # broad spectrum exception to trap anticipated short term issues with BMT validation
                logger.error(f"BMT validate_qualifier Exception: {str(e)}")
                self.report(
                    code=f"error.{context}.qualifier.invalid",
                    source_trail=source_trail,
                    identifier=edge_id,
                    qualifier_type_id=qualifier_type_id,
                    qualifier_value=qualifier_value,
                    reason=str(e)
                )

    def validate_qualifiers(
            self,
            edge_id: str,
            edge: Dict,
            associations: Optional[List[str]] = None,
            source_trail: Optional[str] = None
    ):
        """
        Validate Knowledge Edge Qualifiers.

        :param edge_id: str, string identifier for the edge (for reporting purposes)
        :param edge: Dict, the edge object associated with some attributes are expected to be found
        :param associations: Optional[List[str]], Biolink association subclasses possibly related to the current edge.
        :param source_trail, Optional[str], audit trail of knowledge source provenance for a given Edge, as a string.
                             Defaults to "global" if not specified.
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
        elif self.validate_biolink():
            qualifiers: List = edge['qualifiers']
            self.validate_qualifier_entry(
                context="knowledge_graph.edge.qualifiers",
                edge_id=edge_id,
                qualifiers=qualifiers,
                associations=associations,
                source_trail=source_trail
            )

    def validate_qualifier_constraints(
            self,
            edge_id: str,
            edge: Dict
    ):
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
                elif self.validate_biolink():
                    # We have a putative non-empty 'qualifier_set'
                    qualifier_set: List = qualifier_set_entry['qualifier_set']
                    self.validate_qualifier_entry(
                        context="query_graph.edge.qualifier_constraints.qualifier_set",
                        edge_id=edge_id,
                        qualifiers=qualifier_set
                    )

    def validate_infores(self, context: str, edge_id: str, identifier: str) -> bool:
        """
        Validate that the specified identifier is a well-formed Infores CURIE.
        Note that here we also now accept that the identifier can
        be a semicolon delimited list of such infores.

        :param context: reporting context as specified by a validation code prefix
        :param edge_id: specific edge validated, for the purpose of reporting validation context
        :param identifier: candidate (list of) infores curie(s) to be validated.
        :return:
        """
        code_prefix: str = f"error.knowledge_graph.edge.sources.retrieval_source.{context}.infores"

        # sanity check...
        if not identifier:
            # identifier itself is None or empty string
            self.report(
                code=f"{code_prefix}.missing",
                edge_id=edge_id
            )
            return False

        # For uniform processing here, we treat every identifier
        # as a potential list (even if only a list of one entry),
        ids: list[str] = [token.strip() for token in identifier.split(";")]
        if not all([i for i in ids]):
            # if the identifier is a semicolon delimited array,
            # then at least one of the entries is None or empty...
            self.report(
                code=f"{code_prefix}.missing",
                identifier=identifier,
                edge_id=edge_id
            )
            return False

        if not all([is_curie(i) for i in ids]):
            # ... or at least one of the entries is not a CURIE...
            self.report(
                code=f"{code_prefix}.not_curie",
                identifier=identifier,
                edge_id=edge_id
            )
            return False

        if not all([i.startswith("infores:") for i in ids]):
            # ... or at least one of the entries is not a CURIE...
            self.report(
                code=f"{code_prefix}.invalid",
                identifier=identifier,
                edge_id=edge_id
            )
            return False

        # TODO: infores is causing too much instability for now so support has been removed from BMT
        # TODO: reimplement using YAML version of infores catalog
        # if not self.bmt.get_infores_details(identifier):
        #     # if this method returns 'None' then this is an unregistered infores?
        #     self.report(
        #         code=f"{code_prefix}.unknown",
        #         identifier=identifier,
        #         edge_id=edge_id
        #     )
        #     return False

        # Infores validates properly here
        return True

    def validate_sources(self, edge_id: str, edge: Dict) -> Optional[str]:
        """
        Validate (TRAPI 1.4.0-beta ++) Edge sources provenance.

        :param edge_id: str, string identifier for the edge (for reporting purposes)
        :param edge: Dict, the edge object associated with some attributes are expected to be found
        :return: Optional[str], audit trail of knowledge source provenance for a given Edge, as a string.
        """
        sources: Dict[str, List[str]] = dict()
        # we ought not to have to test for the absence of the "sources" tag
        # if general TRAPI schema validation is run, since it will catch such missing data
        # however, this method may be directly run on invalid TRAPI data, so...
        if "sources" not in edge:
            self.report(code="error.knowledge_graph.edge.sources.missing", identifier=edge_id)
        elif not edge["sources"]:
            # Cardinality of "sources" array is also validated by the TRAPI schema
            # but for the same reasons noted above, we check again here.
            self.report(code="error.knowledge_graph.edge.sources.empty", identifier=edge_id)
        elif not isinstance(edge["sources"], List):
            self.report(code="error.knowledge_graph.edge.sources.not_array", identifier=edge_id)
        else:
            # by this point, we have verified that we have a "sources" list of
            # at least one (hopefully properly formatted RetrievalSource) entry
            edge_sources = edge["sources"]

            # The RetrievalSource items in the "sources" array is also partially validated insofar as JSONSchema can
            # validate based on the TRAPI schema; however, some kinds of validation are either not deterministic from
            # the schema. The remainder of this method validates an initial basic 'semantic' subset of RetrievalSource
            # content for which the validation is both easy and deemed generally useful. This includes detection of
            # anticipated Edge provenance roles (i.e. mandatory 'primary' and tests against expected provenance tags)
            # and the capture of the 'provenance audit trail' of sources, for reporting purposes

            # Method caller associated Edge sources to be checked

            ara_source: Optional[str]
            kp_source: Optional[str]
            kp_source_type: Optional[str]
            ara_source, kp_source, kp_source_type = self.get_target_provenance()

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
                if not self. validate_infores(
                        context="resource_id",
                        edge_id=edge_id,
                        identifier=resource_id
                ):
                    # if not validated, we should probably not
                    # continue using the 'resource_id' from here
                    continue

                else:
                    # start capturing the "sources" audit trail here
                    if resource_id not in sources:
                        sources[resource_id] = list()

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

                                if not self.validate_infores(
                                    context="upstream_resource_ids",
                                    edge_id=edge_id,
                                    identifier=identifier
                                ):
                                    # if not validated, we should probably not
                                    # continue using the 'identifier' from here
                                    continue

                                else:
                                    if identifier == ara_source:
                                        found_ara_knowledge_source = True

                                    # we don't worry about kp_source_type here since it is
                                    # not directly annotated with the upstream_resource_ids
                                    if identifier == kp_source:
                                        found_kp_knowledge_source = True

                                    # Capture the upstream 'upstream_resource_id' source here
                                    sources[resource_id].append(identifier)

                    # 4. If provided (Optional), we *could* check the optional 'source_record_urls'
                    #    if they are all resolvable URLs (but maybe we do not attempt this for now...)
                    #
                    # if "source_record_urls" in retrieval_source:
                    #     source_record_urls: Optional[List[str]] = retrieval_source["source_record_urls"]

            # After all the "sources" RetrievalSource entries have been scanned,
            # then perform a complete validation check for complete expected provenance.
            source_trail: Optional[str] = self.build_source_trail(sources) if sources else None

            self.validate_provenance(
                edge_id,
                ara_source, found_ara_knowledge_source,
                kp_source, found_kp_knowledge_source, kp_source_type,
                found_primary_knowledge_source,
                source_trail=source_trail
            )

            return source_trail  # may be empty if required RetrievalSource 'sources' entries are missing

    # TODO: 11-Sept-2023: Certain specific 'mixin' predicates used in
    #       Knowledge or Query Graphs are being validated for now
    #       as 'warnings', for short term validation purposes
    #       (see reasoner-validator issue #97)
    PREDICATE_INCLUSIONS = ["biolink:interacts_with", 'biolink:treats']

    def validate_predicate(
            self,
            edge_id: str,
            predicate: str,
            graph_type: TRAPIGraphType,
            source_trail: Optional[str] = None
    ):
        """
        Validates predicates based on their meta-nature: existence, mixin,
        deprecation, etc. with some notable hard-coded explicit
        PREDICATE_INCLUSIONS exceptions in earlier Biolink Model releases.

        :param edge_id: str, identifier of the edge whose predicate is being validated
        :param predicate: str, putative Biolink Model predicate to be validated
        :param source_trail: str, putative Biolink Model predicate to be validated
        :param graph_type: TRAPIGraphType, type of TRAPI graph component being validated
        :return: None (validation communicated via class instance of method)
        """
        # PREDICATE_INCLUSIONS provides for selective override of
        # validation of particular predicates prior to Biolink 4.2.1
        if self.minimum_required_biolink_version("4.2.1") or \
                predicate not in self.PREDICATE_INCLUSIONS:

            graph_type_context: str = graph_type.name.lower()
            if graph_type_context != "input_edge":
                graph_type_context += ".edge"
            context: str = f"{graph_type_context}.predicate"

            # Validate the putative predicate as
            # *not* being abstract, deprecated or
            # a mixin (for Biolink Model release >= 4.2.1?)
            biolink_class = self.validate_element_status(
                graph_type=graph_type,
                context=context,
                identifier=predicate,
                edge_id=edge_id,
                source_trail=source_trail,

                # validation of 'predicates' can ignore graph type
                # unless strict validation is globally overridden
                ignore_graph_type=True
            )
            if biolink_class:
                if not self.bmt.is_predicate(predicate):
                    self.report(
                        code=f"error.{context}.invalid",
                        source_trail=source_trail,
                        identifier=predicate,
                        edge_id=edge_id
                    )
                elif self.minimum_required_biolink_version("2.2.0") and \
                        not self.bmt.is_translator_canonical_predicate(predicate):
                    self.report(
                        code=f"warning.{context}.non_canonical",
                        source_trail=source_trail,
                        identifier=predicate,
                        edge_id=edge_id
                    )

    @staticmethod
    def build_source_trail(sources: Optional[Dict[str, List[str]]]) -> Optional[str]:
        """
        Returns a 'source_trail' path from 'primary_knowledge_source' upwards. The "sources" should
        have at least one and only one primary knowledge source (with an empty 'upstream_resource_ids' list).

        :param sources: Optional[Dict[str, List[str]]], catalog of upstream knowledge sources indexed by resource_id's
        :return: Optional[str] source ("audit") trail ('path') from primary to topmost wrapper knowledge source infores
        """
        if sources:
            # Example "sources"...:
            # {
            #     "infores:chebi": [],
            #     "infores:biothings-explorer": ["infores:chebi"],
            #     "infores:molepro": ["infores:biothings-explorer"],
            #     "infores:arax": ["infores:molepro"]
            # }
            #
            source_paths: Dict = {
                upstream_resource_ids[0] if upstream_resource_ids else "primary": downstream_id
                for downstream_id, upstream_resource_ids in sources.items()
            }

            # ...reversed and flattened into "source_paths"...:
            # {
            #     "infores:biothings-explorer": "infores:molepro",
            #     "infores:chebi": "infores:biothings-explorer",
            #     "infores:molepro": "infores:arax",
            #     "primary": "infores:chebi"
            # }
            current_resource = source_paths["primary"] if "primary" in source_paths else None
            # current_resource == "infores:chebi"  # could be 'None' if no primary resources available?
            source_trail: Optional[str] = None
            if current_resource is not None:
                source_trail = current_resource
                while True:
                    if current_resource in source_paths:
                        current_resource = source_paths[current_resource]
                        source_trail += f" -> {current_resource}"
                    else:
                        break  # this should 'break' at "infores:arax"
            else:
                # Missing the primary resource? With a bit more effort
                # Infer the path from the other direction?
                reverse_source_path: Dict = dict()
                for upstream_id, downstream_id in source_paths.items():
                    if downstream_id not in source_paths:
                        source_trail = f"{upstream_id} -> {downstream_id}"
                        current_resource = upstream_id
                    else:
                        reverse_source_path[downstream_id] = upstream_id

                while True:
                    if current_resource in reverse_source_path:
                        current_resource = reverse_source_path[current_resource]
                        source_trail = f"{current_resource} -> " + source_trail
                    else:
                        break

            # "infores:chebi -> infores:biothings-explorer -> infores:molepro -> infores:arax"
            return source_trail
        else:
            return None

    def is_treats(self, predicate: Optional[str]) -> bool:
        if not predicate:
            return False
        return predicate in self.bmt.get_descendants("treats", formatted=True)

    def validate_graph_edge(self, edge: Dict, graph_type: TRAPIGraphType):
        """
        Validate slot properties of a relationship ('biolink:Association') edge.

        :param edge: Dict[str, str], dictionary of slot properties of the edge.
        :param graph_type: TRAPIGraphType, type of TRAPI component being validated
        """
        # logger.debug(edge)
        # edge data fields to be validated...
        subject_id = edge['subject'] if 'subject' in edge else None
        subject_categories: Optional[List[str]] = self.get_node_categories(node_id=subject_id)

        predicates: Optional[List[str]]
        predicate: Optional[str] = None
        if graph_type is TRAPIGraphType.Knowledge_Graph:
            predicate = edge['predicate'] if 'predicate' in edge else None
            edge_label = predicate
            predicates = [predicate]
        else:
            # Query Graph...
            predicates = edge['predicates'] if 'predicates' in edge else None
            edge_label = str(predicates)

        object_id = edge['object'] if 'object' in edge else None
        object_categories: Optional[List[str]] = self.get_node_categories(node_id=object_id)

        edge_id = f"{str(subject_id)}[{'|'.join(subject_categories) if subject_categories else 'None'}]" +\
                  f"--{edge_label}->" +\
                  f"{str(object_id)}[{'|'.join(object_categories) if object_categories else 'None'}]"

        context: str = graph_type.name.lower()

        # 7 July 2023: since edge provenance annotation is somewhat
        # orthogonal to the contents of the edge itself, we move the
        # attribute validation ahead of Edge semantic validation,
        # which allows us to capture the Edge provenance audit trail
        # for reasoner-validator issue#86 - edge sources reporting.
        #
        # Validate edge attributes (or attribute_constraints)
        # and (Biolink) edge qualifiers (or qualifier_constraints)
        source_trail: Optional[str] = None
        if graph_type is TRAPIGraphType.Knowledge_Graph:

            # Edge provenance "sources" field is only recorded
            # as an Edge property, from TRAPI 1.4.0-beta onwards
            if self.minimum_required_trapi_version("1.4.0-beta"):
                # For TRAPI 1.4.0, the 'source_trail' is parsed in by 'validate_sources'...
                source_trail = self.validate_sources(edge_id=edge_id, edge=edge)

                # ...then the 'validate_sources' computed 'source_trail' is communicated
                #    to 'validate_attributes' for use in attribute validation reporting
                self.validate_attributes(
                    graph_type=graph_type,
                    edge_id=edge_id,
                    edge=edge,
                    source_trail=source_trail
                )
            else:
                # For TRAPI 1.3.0, the 'sources' are discovered internally by 'validate_attributes'
                # and the resulting source_trail returned, for further external reporting purposes
                source_trail = self.validate_attributes(graph_type=graph_type, edge_id=edge_id, edge=edge)

            associations: Optional[List[str]] = None
            if self.validate_biolink():
                # We need to look up the biolink:Association subclass
                # matching the subject and object categories of the edge.
                # We don't here filter for empty *_categories, so in some
                # fringe cases, misleading downstream validation may occur.
                associations = self.bmt.get_associations(
                    subject_categories=subject_categories,
                    predicates=predicates,
                    object_categories=object_categories,
                    formatted=True
                )

            # Edge "qualifiers" field is only recorded as an
            # Edge property, from TRAPI 1.3.0-beta onwards
            if self.minimum_required_trapi_version("1.3.0-beta"):
                self.validate_qualifiers(
                    edge_id=edge_id,
                    edge=edge,
                    associations=associations,
                    source_trail=source_trail
                )

        else:
            # NOT a Knowledge Graph edge validation
            self.validate_attribute_constraints(edge_id=edge_id, edge=edge)

            # Edge "qualifiers" field is only recorded as an
            # Edge property, from TRAPI 1.3.0-beta onwards
            # We don't care about 'source_trail' here, for the Query Graph edges
            if self.minimum_required_trapi_version("1.3.0-beta"):
                self.validate_qualifier_constraints(edge_id=edge_id, edge=edge)

        # Validate Subject node
        if not subject_id:
            # This message may no longer be triggered
            # for TRAPI release >= 1.4-beta since the
            # schema deems the Edge.subject 'nullable: false'
            self.report(
                code=f"error.{context}.edge.subject.missing",
                source_trail=source_trail,
                identifier=edge_id
            )

        elif subject_id not in self.get_node_identifiers():
            self.report(
                code=f"error.{context}.edge.subject.missing_from_nodes",
                source_trail=source_trail,
                identifier=subject_id,
                edge_id=edge_id
            )
        else:
            self.count_node(node_id=subject_id)

        # Validate Predicates
        if graph_type is TRAPIGraphType.Knowledge_Graph:
            if not predicate:
                self.report(
                    code="error.knowledge_graph.edge.predicate.missing",
                    source_trail=source_trail,
                    context=graph_type.value,
                    identifier=edge_id
                )
            elif self.validate_biolink():
                self.validate_predicate(
                    edge_id=edge_id,
                    predicate=predicate,
                    graph_type=graph_type,
                    source_trail=source_trail
                )

        else:  # is a Query Graph...
            if predicates is None:
                # Query Graphs can have a missing or null predicates slot
                pass
            elif not isinstance(predicates, List):
                self.report(
                    code="error.query_graph.edge.predicate.not_array",
                    source_trail=source_trail,
                    identifier=edge_id
                )
            elif len(predicates) == 0:
                self.report(
                    code="error.query_graph.edge.predicate.empty_array",
                    source_trail=source_trail,
                    identifier=edge_id
                )
            elif self.validate_biolink():
                # Should now be a non-empty list of CURIES
                # which should validate as Biolink Predicates
                for predicate in predicates:
                    if not predicate:
                        continue  # sanity check
                    self.validate_predicate(
                        edge_id=edge_id,
                        predicate=predicate,
                        graph_type=graph_type,
                        source_trail=source_trail
                    )

        # Validate Object Node
        if not object_id:
            # This message may no longer be triggered
            # for TRAPI release >= 1.4-beta since the
            # schema deems the Edge.object 'nullable: false'
            self.report(
                code=f"error.{context}.edge.object.missing",
                source_trail=source_trail,
                identifier=edge_id
            )
        elif object_id not in self.get_node_identifiers():
            self.report(
                code=f"error.{context}.edge.object.missing_from_nodes",
                source_trail=source_trail,
                identifier=object_id,
                edge_id=edge_id
            )
        else:
            self.count_node(node_id=object_id)

    # TODO: 11-July-2023: Certain specific 'abstract' or 'mixin' categories used in Knowledge Graphs
    #                     are being validated for now as 'warnings', for short term validation purposes
    CATEGORY_INCLUSIONS = ["biolink:BiologicalEntity", "biolink:InformationContentEntity"]

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
                # 'category' is known to Biolink... good start!
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

        if 'subject_id' in edge:
            subject_curie = edge['subject_id']
        elif 'subject' in edge:
            subject_curie = edge['subject']
        else:
            subject_curie = None

        if 'object_id' in edge:
            object_curie = edge['object_id']
        elif 'object' in edge:
            object_curie = edge['object']
        else:
            object_curie = None

        edge_id = f"{str(subject_curie)}[{str(subject_category_curie)}]" + \
                  f"--{predicate}->{str(object_curie)}[{str(object_category_curie)}]"

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
            self.validate_predicate(edge_id=edge_id, predicate=predicate, graph_type=TRAPIGraphType.Input_Edge)

        self.validate_input_edge_node(
            context='Object',
            node_id=object_curie,
            category_name=object_category_curie
        )

    def check_biolink_model_compliance(self, graph: Dict, graph_type: TRAPIGraphType):
        """
        Validate a TRAPI-schema compliant Message graph-like data structure
        against the currently active Biolink Model Toolkit model version.

        :param graph: Dict, knowledge graph to be validated
        :param graph_type: TRAPIGraphType, component type of TRAPI graph to be validated
        """
        if not graph:
            self.report(code="warning.graph.empty", identifier=graph_type.value)
            return  # nothing really more to do here!

        # Access graph data fields to be validated
        nodes: Optional[Dict]
        if 'nodes' in graph and graph['nodes']:
            nodes = graph['nodes']
        else:
            # Query Graphs can have an empty nodes catalog
            if graph_type is not TRAPIGraphType.Query_Graph:
                self.report(code="error.knowledge_graph.nodes.empty")
            # else:  Query Graphs can omit the 'nodes' tag
            nodes = None

        edges: Optional[Dict]
        if 'edges' in graph and graph['edges']:
            edges = graph['edges']
        else:
            if graph_type is not TRAPIGraphType.Query_Graph:
                self.report(code="error.knowledge_graph.edges.empty")
            # else:  Query Graphs can omit the 'edges' tag
            edges = None

        self.reset_node_info(graph_type=graph_type)
        if nodes:
            for node_id, details in nodes.items():
                self.validate_graph_node(node_id, details, graph_type=graph_type)

            # A dictionary of instances of 'node_id', associated 'categories' plus an
            # internal counter, are needed for the subsequent edge validation processes
            self.set_nodes(nodes)

            if edges:
                for edge in edges.values():
                    # print(f"{str(edge)}", flush=True)
                    self.validate_graph_edge(edge, graph_type=graph_type)

        if not self.has_valid_node_information(graph_type=graph_type):
            self.report(code=f"error.{graph_type.label()}.nodes.uninformative")

        # dangling edges are discovered during validate_graph_edge() but
        # dangling_nodes can only be detected after all edges are processed
        # Release This is now deemed not a serious error but will be treated as 'info'
        dangling_nodes: List[str] = self.has_dangling_nodes()
        if dangling_nodes:
            self.report(
                code=f"warning.{graph_type.label()}.nodes.dangling",
                # this is an odd kind of identifier but the best we can do here?
                identifier='|'.join(dangling_nodes)
            )

    def merge(self, reporter):
        """
        Merge all messages and metadata from a second BiolinkValidator,
        into the calling TRAPISchemaValidator instance.

        :param reporter: second BiolinkValidator
        """
        TRAPISchemaValidator.merge(self, reporter)

        # First come, first serve... We only overwrite
        # empty versions in the parent reporter
        if isinstance(reporter, BiolinkValidator) and not self.get_biolink_version():
            self.reset_biolink_version(reporter.get_biolink_version())

    def to_dict(self) -> Dict:
        """
        Export BiolinkValidator contents as a Python dictionary
        (including Biolink version and parent class dictionary content).
        :return: Dict
        """
        dictionary = TRAPISchemaValidator.to_dict(self)
        dictionary["biolink_version"] = self.get_biolink_version()
        return dictionary

    def report_header(self, title: Optional[str] = None, compact_format: bool = True) -> str:
        header: str = super().report_header(title, compact_format)
        header += " and Biolink Model version " \
                  f"'{str(self.get_biolink_version() if self.get_biolink_version() is not None else 'Default')}'"
        return header
