# Validation Codes Dictionary

## Critical Error

### critical.trapi.validation

**Message:** Schema validation error

**Context:** identifier, component, reason

**Description:** Critical JSON Schema validation error reported for specified TRAPI query component.

### critical.trapi.request.invalid

**Message:** Test could not generate a valid TRAPI query request object using identified element

**Context:** identifier, test, reason

**Description:** Specified TRAPI query unit 'test' query could not be prepared for the indicated reason, using the identified Biolink starting element.

### critical.trapi.response.unexpected_http_code

**Message:** Unexpected HTTP status code

**Context:** identifier

**Description:** TRAPI query attempt returned an abnormal (non-200) server HTTP status code as noted.

## Error

### error.biolink.model.noncompliance

**Message:** S-P-O statement is not compliant to Biolink Model release

**Context:** identifier, biolink_release

**Description:** This knowledge statement is not compliant to the specified release of the Biolink Model. Review associated messages for underlying cause!

### error.trapi.response.empty

**Message:** TRAPI Response is missing!

**Description:** TRAPI Response to be validated should not be totally empty but should have a Message body.

### error.trapi.response.message.empty

**Message:** TRAPI Response missing its Message!

**Description:** TRAPI response should at least have non-empty original TRAPI request Message in its reply.

### error.trapi.response.query_graph.missing

**Message:** TRAPI Message is missing its Query Graph!

**Description:** TRAPI response should generally have a TRAPI request message Query Graph key value in its reply.

### error.trapi.response.query_graph.empty

**Message:** Response returned an empty Message Query Graph!

**Description:** TRAPI response should at least have non-empty original TRAPI request message Query Graph in its reply.

### error.trapi.response.knowledge_graph.missing

**Message:** TRAPI Message is missing its Knowledge Graph component!

**Description:** TRAPI response should generally have a TRAPI request message Knowledge Graph key value in its reply.

### error.trapi.response.knowledge_graph.missing_expected_edge

**Message:** Knowledge Graph of TRAPI Response Message is missing expected Edge

**Context:** identifier

**Description:** The given TRAPI Response is expected to return specific edge(s) relating to the original (test edge?) data used to prepare the TRAPI Request!

### error.trapi.response.knowledge_graph.empty

**Message:** Response returned an empty Message Knowledge Graph, which is an error in this context!

**Description:** An empty Knowledge Graph is considered an error in this validation context!

### error.trapi.response.results.missing

**Message:** TRAPI Message is missing its Results component!

**Description:** TRAPI response should generally have a TRAPI request message Request key value in its reply.

### error.trapi.response.results.non_array

**Message:** Response returned a non-array Message.Results!

**Description:** TRAPI Message.Results must be an array data type (even if empty)

### error.trapi.response.results.missing_bindings

**Message:** Result object IDs for output node binding did not return the original identifier nor aliases for input id

**Context:** identifier, output_node_binding

**Description:** TRAPI Message.Results cannot resolve its reported identifier mappings to the original query.

### error.input_edge.node.category.missing

**Message:** Category missing for node

**Context:** identifier

**Description:** Category value must be specified in an input test data edge!

### error.input_edge.node.category.not_a_category

**Message:** Asserted category is not a proper category class for node

**Context:** node_id, identifier

**Description:** Category specified in input test data edge node is not recorded as a category term in specified version of Biolink. Replace with a known category!

### error.input_edge.node.category.unknown

**Message:** Node has unknown category

**Context:** node_id, identifier

**Description:** Category specified in input test data edge node is not a model element recorded in specified version of Biolink. Replace with a known category!

### error.input_edge.node.id.missing

**Message:** Node identifier is missing for node

**Context:** identifier

**Description:** Input test data edge data needs to have a specific node identifier for testing!

### error.input_edge.predicate.missing

**Message:** Edge has missing or empty predicate

**Context:** identifier

**Description:** Input test edge data needs to have a specific edge predicate for testing!

### error.input_edge.predicate.unknown

**Message:** Edge has unknown predicate

**Context:** edge_id, identifier

**Description:** Predicate specified in input test data edge is not recorded in specified version of Biolink. Replace with a known predicate!

### error.input_edge.predicate.abstract

**Message:** Edge is not permitted to have 'abstract' predicate

**Context:** edge_id, identifier

**Description:** Edge data validation is currently strict: predicates cannot be 'abstract'! Replace with a concrete predicate.

### error.input_edge.predicate.mixin

**Message:** Edge is not permitted to have an 'mixin' predicate

**Context:** edge_id, identifier

**Description:** Edge data validation is currently strict: predicates cannot be of type 'mixin'! Replace with a concrete predicate.

### error.input_edge.predicate.invalid

**Message:** Edge has invalid predicate

**Context:** edge_id, identifier

**Description:** Predicate specified in Input Edge is not defined as a predicate in specified version of Biolink. Replace with a proper predicate!

### error.query_graph.node.category.missing

**Message:** Category is missing from node

**Context:** identifier

**Description:** Category value must be specified in an query graph edge!

### error.query_graph.node.category.not_a_category

**Message:** Node has invalid category

**Context:** node_id, identifier

**Description:** Category specified in query graph edge node is not recorded as a category term in specified version of Biolink. Replace with a known category!

### error.query_graph.node.category.unknown

**Message:** Node has unknown category

**Context:** node_id, identifier

**Description:** Category specified in query graph edge node is not a model element recorded in specified version of Biolink. Replace with a known category!

### error.query_graph.node.ids.not_array

**Message:** The 'ids' property value is not an array in node

**Context:** identifier

**Description:** Value of 'ids' property in Query Graph node must be an array data type (even if empty)!

### error.query_graph.node.categories.not_array

**Message:** The 'categories' property value is not an array in node

**Context:** identifier

**Description:** Value of 'categories' property in Query Graph node must be an array data type (even if empty)!

### error.query_graph.node.is_set.not_boolean

**Message:** The 'is_set' property is not a boolean value in node

**Context:** identifier

**Description:** The 'is_set' field in node of Query Graph, if present, must be a boolean value!

### error.query_graph.edge.subject.missing

**Message:** The 'subject' property value is missing or empty in Edge

**Context:** identifier

**Description:** Edge must have a 'subject' key with a non-empty associated value!

### error.query_graph.edge.subject.missing_from_nodes

**Message:** The nodes catalog of query graph for missing the subject id recorded on Edge

**Context:** edge_id, identifier

**Description:** Every 'subject' identifier of every edge in a Query Graph must also be recorded in the list of nodes for that graph!

### error.query_graph.edge.object.missing

**Message:** The 'object' property value is missing or empty in Edge

**Context:** identifier

**Description:** Edge must have a 'object' key with a non-empty associated value!

### error.query_graph.edge.object.missing_from_nodes

**Message:** The nodes catalog of query graph for missing the object id recorded on Edge

**Context:** edge_id, identifier

**Description:** Every 'object' identifier of every edge in a Query Graph must also be recorded in the list of nodes for that graph!

### error.query_graph.edge.predicate.missing

**Message:** Predicate is missing or empty for Edge

**Context:** identifier

**Description:** The predicate of Query Graph edge needs to specified using a 'predicate' key with an array list of one or more predicates!

### error.query_graph.edge.predicate.unknown

**Message:** Edge has unknown predicate

**Context:** edge_id, identifier

**Description:** Predicate specified in Query Graph edge is not defined in specified version of Biolink. Replace with a defined predicate!

### error.query_graph.edge.predicate.not_array

**Message:** Predicate property value is not an array for Edge

**Context:** identifier

**Description:** Value of 'predicate' property value in Query Graph must be an array data type!

### error.query_graph.edge.predicate.empty_array

**Message:** Predicate property value is an empty array for Edge

**Context:** identifier

**Description:** Value of 'predicate' array property value in Query Graph must contain one or more predicates!

### error.query_graph.edge.predicate.abstract

**Message:** Edge is not permitted to have an 'abstract' predicate

**Context:** edge_id, identifier

**Description:** Query Graph data validation is currently strict: cannot have 'abstract' predicates! Replace with a concrete predicate.

### error.query_graph.edge.predicate.mixin

**Message:** Edge is not permitted to have an 'mixin' predicate

**Context:** edge_id, identifier

**Description:** Query Graph data validation is currently strict: cannot have 'mixin' predicates! Replace with a concrete predicate.

### error.query_graph.edge.predicate.invalid

**Message:** Edge has invalid predicate

**Context:** edge_id, identifier

**Description:** Predicate specified in Query Graph edge is not defined as a predicate in specified version of Biolink. Replace with a proper predicate!

### error.query_graph.edge.attribute_constraints.not_array

**Message:** Attribute_constraints property value is not an array for Edge

**Context:** identifier

**Description:** Value of 'attribute_constraints' property value in a Query Graph must be an array data type!

### error.query_graph.edge.qualifier_constraints.qualifier_set.empty

**Message:** Qualifier_set property value is empty for Edge

**Context:** identifier

**Description:** Value of a 'qualifier_constraints.qualifier_set' property in a Query Graph must not be non-empty array!

### error.query_graph.edge.qualifier_constraints.qualifier_set.qualifier.type_id.unknown

**Message:** Edge has unknown qualifier_type_id

**Context:** edge_id, identifier

**Description:** A qualifier qualifier_type_id must be defined in the specified version of Biolink!

### error.query_graph.edge.qualifier_constraints.qualifier_set.qualifier.value.not_a_predicate

**Message:** Qualifier_type_id 'biolink:qualified_predicate' for edge has a qualifier_value which is not a Biolink predicate.

**Context:** identifier, qualifier_value

**Description:** The 'qualifier_value' for 'biolink:qualified_predicate' should be a Biolink predicate term!

### error.query_graph.edge.qualifier_constraints.qualifier_set.qualifier.invalid

**Message:** Validation of qualifier in a qualifier_constraints qualifier_set threw an unexpected exception!

**Context:** identifier, qualifier_type_id, qualifier_value, reason

**Description:** Validation of a specified 'qualifier_type_id' and 'qualifier_value' failed for a given exceptional reason!

### error.knowledge_graph.nodes.empty

**Message:** No nodes found!

**Description:** Knowledge graph in TRAPI messages must have a 'nodes' key and non-empty associated value!

### error.knowledge_graph.edges.empty

**Message:** No edges found!

**Description:** Knowledge graph in TRAPI messages must have a 'edges' key and non-empty associated value!

### error.knowledge_graph.node.category.missing

**Message:** Category is missing for node

**Context:** identifier

**Description:** Category value must be specified in an knowledge graph edge!

### error.knowledge_graph.node.category.not_a_category

**Message:** Node has invalid category

**Context:** node_id, identifier

**Description:** Category specified in knowledge graph edge node is not recorded as a category term in specified version of Biolink. Replace with a known category!

### error.knowledge_graph.node.category.unknown

**Message:** Node has unknown category

**Context:** node_id, identifier

**Description:** Category specified in knowledge graph edge node is not a model element recorded in specified version of Biolink. Replace with a known category!

### error.knowledge_graph.node.id.missing

**Message:** Node identifier is missing for node

**Context:** identifier

**Description:** Knowledge graph node must have a 'id' key with a non-empty associated value!

### error.knowledge_graph.node.missing_categories

**Message:** Categories are missing for node

**Context:** identifier

**Description:** Knowledge graph node must have a 'categories' key with a non-empty associated value!

### error.knowledge_graph.node.ids.not_array

**Message:** The 'ids' property value is not an array for node

**Context:** identifier

**Description:** Value of 'ids' property in Query Graph node must be an array data type!

### error.knowledge_graph.node.empty_ids

**Message:** The 'ids' property array is empty for node

**Context:** identifier

**Description:** Value of 'ids' array property in Knowledge Graph node must contain one or more node identifiers!

### error.knowledge_graph.node.categories.not_array

**Message:** The categories property value is not an array for node

**Context:** identifier

**Description:** Value of 'categories' property in Knowledge Graph node must be an array data type!

### error.knowledge_graph.node.categories.not_concrete

**Message:** None of the asserted categories are concrete for node

**Context:** identifier, categories

**Description:** Categories specified in knowledge graph edge node may not resolve to any (non-abstract, non-mixin) category terms in the specified version of Biolink. Add at least one 'concrete' category (as the most specific category?)!

### error.knowledge_graph.node.empty_categories

**Message:** The 'categories' property array is empty for node

**Context:** identifier

**Description:** Value of 'categories' array property in Knowledge Graph node must contain one or more node category terms!

### error.knowledge_graph.node.is_set.not_boolean

**Message:** The 'is_set' property is not a boolean value for node

**Context:** identifier

**Description:** The 'is_set' field in node of Knowledge Graph, if present, must be a boolean value!

### error.knowledge_graph.edge.subject.missing

**Message:** The 'subject' property value is missing or empty for Edge

**Context:** identifier

**Description:** Edge must have a 'subject' key with a non-empty associated value!

### error.knowledge_graph.edge.subject.missing_from_nodes

**Message:** The nodes catalog of query graph for missing the subject id recorded on Edge

**Context:** edge_id, identifier

**Description:** Every 'subject' identifier of every edge in a Knowledge Graph must also be recorded in the list of nodes for that graph!

### error.knowledge_graph.edge.object.missing

**Message:** The 'object' property value  is missing or empty for Edge

**Context:** identifier

**Description:** Edge must have a 'object' key with a non-empty associated value!

### error.knowledge_graph.edge.object.missing_from_nodes

**Message:** The nodes catalog of query graph for missing the object id recorded on Edge

**Context:** edge_id, identifier

**Description:** Every 'object' identifier of every edge in a Knowledge Graph must also be recorded in the list of nodes for that graph!

### error.knowledge_graph.edge.predicate.missing

**Message:** The predicate is missing or empty for Edge

**Context:** identifier

**Description:** Edge must have a 'predicate' key with a non-empty associated value!

### error.knowledge_graph.edge.predicate.unknown

**Message:** Edge has unknown predicate

**Context:** edge_id, identifier

**Description:** Predicate specified in Knowledge Graph edge is not defined in specified version of Biolink. Replace with a defined predicate!

### error.knowledge_graph.edge.predicate.invalid

**Message:** Edge has invalid predicate

**Context:** edge_id, identifier

**Description:** Predicate specified in Knowledge Graph edge is not defined as a predicate in specified version of Biolink. Replace with a defined predicate!

### error.knowledge_graph.edge.predicate.not_array

**Message:** The predicate property value is not an array for Edge

**Context:** identifier

**Description:** Value of the 'predicate' property in Knowledge Graph edge must be an array data type!

### error.knowledge_graph.edge.predicate.empty_array

**Message:** The predicate property value is an empty array for Edge

**Context:** identifier

**Description:** Value of the 'predicate' array property in Knowledge Graph edge must contain one or more predicates!

### error.knowledge_graph.edge.predicate.abstract

**Message:** Edge is not permitted to have an 'abstract' predicate

**Context:** edge_id, identifier

**Description:** Knowledge Graph data validation is currently strict: cannot have 'abstract' predicates! Replace with a concrete predicate.

### error.knowledge_graph.edge.predicate.mixin

**Message:** Edge is not permitted to have an 'mixin' predicate

**Context:** edge_id, identifier

**Description:** Knowledge Graph data validation is currently strict: cannot have 'mixin' predicates! Replace with a concrete predicate.

### error.knowledge_graph.edge.attribute.missing

**Message:** Missing 'attributes' key for Edge

**Context:** identifier

**Description:** Edge must have a 'attributes' key with a non-empty associated value!

### error.knowledge_graph.edge.attribute.empty

**Message:** Empty attributes in Edge

**Context:** identifier

**Description:** Value of 'attributes' property in Knowledge Graph edge must contain a list of one or more attributes!

### error.knowledge_graph.edge.attribute.not_array

**Message:** The attributes are not an array in Edge

**Context:** identifier

**Description:** Value of the 'attributes' property in Knowledge Graph edge must be an array of attributes!

### error.knowledge_graph.edge.attribute.type_id.unknown

**Message:** Edge has unknown attribute_type_id

**Context:** edge_id, identifier

**Description:** Edge Attribute type identifier specified in knowledge graph edge is not recorded in specified version of Biolink. Replace with a known term!

### error.knowledge_graph.edge.attribute.type_id.abstract

**Message:** Edge is not permitted to have an 'abstract' attribute_type_id

**Context:** edge_id, identifier

**Description:** Edge data validation is currently strict: attribute type identifiers cannot be 'abstract'. Replace with a concrete attribute_type_id!

### error.knowledge_graph.edge.attribute.type_id.mixin

**Message:** Edge is not permitted to have an 'mixin' attribute_type_id

**Context:** edge_id, identifier

**Description:** Edge data validation is currently strict: attribute type identifiers cannot be of type 'mixin'. Replace with a concrete attribute_type_id!

### error.knowledge_graph.edge.attribute.type_id.missing

**Message:** An attribute is missing its 'attribute_type_id' property in Edge

**Context:** identifier

**Description:** The attribute of a Knowledge graph edge must have a 'attribute_type_id' key with a non-empty associated value!

### error.knowledge_graph.edge.attribute.type_id.empty

**Message:** An attribute has empty 'attribute_type_id' property in Edge

**Context:** identifier

**Description:** The value of the 'attribute_type_id' of an attribute of a Knowledge graph edge must not be empty!

### error.knowledge_graph.edge.attribute.type_id.not_curie

**Message:** Edge has a value that is not a CURIE for attribute_type_id

**Context:** edge_id, identifier

**Description:** The 'attribute_type_id' of a Knowledge graph edge attribute must be a controlled vocabulary term specified by a CURIE!

### error.knowledge_graph.edge.attribute.value.missing

**Message:** An attribute is missing its 'value' property in Edge

**Context:** identifier

**Description:** An attribute of a Knowledge graph edge must have a 'value' key with a non-empty associated value!

### error.knowledge_graph.edge.attribute.value.empty

**Message:** An attribute has an empty value in Edge

**Context:** identifier

**Description:** The value of an attribute of a Knowledge graph edge must not be empty!

### error.knowledge_graph.edge.provenance.infores.missing

**Message:** Edge has provenance value which is not a well-formed InfoRes CURIE

**Context:** edge_id, identifier

**Description:** The value of an attribute specifying the provenance of a Knowledge graph edge must be the well-formed InfoRes CURIE of a knowledge source!

### error.knowledge_graph.edge.provenance.missing_primary

**Message:** A 'primary' knowledge source is missing for Edge

**Context:** identifier

**Description:** Edge attributes should record the 'infores' identifier of their primary knowledge source provenance with respect to KP.

### error.knowledge_graph.edge.qualifiers.not_array

**Message:** The 'qualifiers' property is not an array in Edge

**Context:** identifier

**Description:** Value of the 'qualifiers' property in Knowledge Graph edge must be an array of attributes!

### error.knowledge_graph.edge.qualifiers.empty

**Message:** The qualifiers property value is empty in Edge

**Context:** identifier

**Description:** Value of a 'qualifiers' property in a Knowledge Graph must not be non-empty array!

### error.knowledge_graph.edge.qualifiers.qualifier.type_id.unknown

**Message:** Edge has unknown qualifier_type_id

**Context:** edge_id, identifier

**Description:** A qualifier qualifier_type_id must be defined in the specified version of Biolink!

### error.knowledge_graph.edge.qualifiers.qualifier.value.unresolved

**Message:** Qualifier_type_id for edge has unresolved qualifier_value

**Context:** edge_id, identifier, qualifier_type_id

**Description:** A 'qualifier_value' for the specified 'qualifier_type_id' of a qualifier likely could not be resolved without knowledge of the edge category!

### error.knowledge_graph.edge.qualifiers.qualifier.value.not_a_predicate

**Message:** Qualifier_type_id 'biolink:qualified_predicate' for edge has a qualifier_value which is not a Biolink predicate.

**Context:** identifier, qualifier_value

**Description:** The 'qualifier_value' for 'biolink:qualified_predicate' should be a Biolink predicate term!

### error.knowledge_graph.edge.qualifiers.qualifier.invalid

**Message:** Validation of qualifier in qualifiers threw an unexpected exception

**Context:** identifier, qualifier_type_id, qualifier_value, reason

**Description:** Validation of a specified 'qualifier_type_id' and 'qualifier_value' failed for a given exceptional reason!

### error.knowledge_graph.edge.sources.missing

**Message:** Missing 'sources' key for Edge

**Context:** identifier

**Description:** Edge must have a 'sources' key with a non-empty associated value!

### error.knowledge_graph.edge.sources.empty

**Message:** Empty 'sources' property in Edge

**Context:** identifier

**Description:** Value of 'sources' property in Knowledge Graph edge must contain a list of one or more RetrievalSource entries!

### error.knowledge_graph.edge.sources.not_array

**Message:** The 'sources' are not an array in Edge

**Context:** identifier

**Description:** Value of the 'sources' property in Knowledge Graph edge must be an array of RetrievalSource entries!

### error.knowledge_graph.edge.sources.retrieval_source.resource_id.infores.not_curie

**Message:** Infores value is not a valid well-formed CURIE

**Context:** edge_id, identifier

**Description:** A 'retrieval_source.resource_id' value must be a well-formed infores CURIE!

### error.knowledge_graph.edge.sources.retrieval_source.resource_id.infores.invalid

**Message:** Invalid Infores namespace

**Context:** edge_id, identifier

**Description:** A 'retrieval_source.resource_id' Infores CURIE must come from the Infores namespace!

### error.knowledge_graph.edge.sources.retrieval_source.resource_id.infores.unknown

**Message:** Unregistered infores

**Context:** edge_id, identifier

**Description:** A 'retrieval_source.resource_id' value must be a registered Infores identifier!

### error.knowledge_graph.edge.sources.retrieval_source.resource_id.empty

**Message:** Empty 'resource_id' property in Edge

**Context:** identifier

**Description:** Value of the 'resource_id' property in the RetrievalSource of a Knowledge Graph Edge must be a non-empty Infores identifier!

### error.knowledge_graph.edge.sources.retrieval_source.upstream_resource_ids.infores.not_curie

**Message:** Infores value is not a valid well-formed CURIE

**Context:** edge_id, identifier

**Description:** A 'retrieval_source.upstream_resource_ids' values must be a well-formed Infores CURIE!

### error.knowledge_graph.edge.sources.retrieval_source.upstream_resource_ids.infores.invalid

**Message:** Invalid Infores namespace

**Context:** edge_id, identifier

**Description:** A 'retrieval_source.upstream_resource_ids' Infores CURIEs must come from the Infores namespace!

### error.knowledge_graph.edge.sources.retrieval_source.upstream_resource_ids.infores.unknown

**Message:** Unregistered Infores

**Context:** edge_id, identifier

**Description:** A 'retrieval_source.upstream_resource_ids' values must be registered infores identifiers!

### error.knowledge_graph.edge.sources.retrieval_source.resource_role.empty

**Message:** Empty 'resource_role' property in Edge

**Context:** identifier

**Description:** Value of the 'resource_role' property in the RetrievalSource of a Knowledge Graph Edge must be a non-empty ResourceRole enum value!

## Warning

### warning.trapi.response.status.unknown

**Message:** TRAPI Response has unrecognized status code

**Context:** identifier

**Description:** The TRAPI Response status code should be one of a standardized set of short codes, e.g. Success, QueryNotTraversable, KPsNotAvailable

### warning.trapi.response.knowledge_graph.empty

**Message:** Response returned an empty Message Knowledge Graph?

**Description:** An empty Knowledge Graph is allowed but merits a boundary response warning?

### warning.trapi.response.results.empty

**Message:** Response returned empty Message.results?

**Description:** Empty Results is allowed but merits a boundary response warning?

### warning.trapi.response.workflow.runner_parameters.null

**Message:** TRAPI Response.workflow.runner_parameters property is missing?

**Description:** If a 'runner_parameters' property value is given for a workflow step specification, it should not be null. This field will be ignored?

### warning.trapi.response.workflow.parameters.null

**Message:** TRAPI Response.workflow.parameters property is missing?

**Description:** If a 'parameters' property value is given for a workflow step specification, it should not be null. This field will be ignored?

### warning.graph.empty

**Message:** Empty graph

**Context:** identifier

**Description:** An empty graph in this particular context is allowed but merits a boundary response warning?

### warning.input_edge.node.category.deprecated

**Message:** Node category had deprecated category

**Context:** node_id, identifier

**Description:** Node category is deprecated in the current model, to be removed in the future. Review Biolink Model for suitable replacement?

### warning.input_edge.node.category.not_concrete

**Message:** Node has unknown, abstract or mixin category

**Context:** node_id, identifier

**Description:** Node category may be unknown, abstract or a mixin in the current model. TRAPI Responses using this edge may not resolve any Knowledge Graph nodes with this category. Review Biolink Model for 'concrete' replacement?

### warning.input_edge.node.id.unmapped_to_category

**Message:** Node identifier found unmapped to target categories for node

**Context:** identifier, unmapped_ids, categories

**Description:** The namespaces of Biolink model node of specified category may be incomplete with respect to identifiers being used in input edge data?

### warning.input_edge.predicate.deprecated

**Message:** Edge has deprecated predicate

**Context:** identifier

**Description:** Input data edge predicate is deprecated in the current model, to be removed in the future. Review Biolink Model for a suitable replacement?

### warning.input_edge.predicate.non_canonical

**Message:** Edge has non-canonical predicate

**Context:** edge_id, identifier

**Description:** A predicate selected for use as input data should preferably be tagged as 'canonical' in the specified Biolink Model release?

### warning.query_graph.node.category.deprecated

**Message:** Node has deprecated category

**Context:** node_id, identifier

**Description:** Node category is deprecated in the current model, to be removed in the future. Review Biolink Model for suitable replacement?

### warning.query_graph.node.ids.unmapped_prefix

**Message:** Node identifiers found unmapped to target categories for node

**Context:** identifier, unmapped_ids, categories

**Description:** One or more node CURIE identifier namespaces are not found among any 'id_prefix' slot values in specified categories in the validating Biolink Model version?

### warning.query_graph.edge.predicate.deprecated

**Message:** Edge has deprecated predicate

**Context:** identifier

**Description:** Edge predicate is deprecated in the current model, to be removed in the future. Review Biolink Model for a suitable replacement?

### warning.query_graph.edge.predicate.non_canonical

**Message:** Edge has non-canonical predicate

**Context:** edge_id, identifier

**Description:** A predicate selected for use in a query graph should preferably be tagged as 'canonical' in the specified Biolink Model release?

### warning.knowledge_graph.node.category.deprecated

**Message:** Node has deprecated category

**Context:** node_id, identifier

**Description:** Node category is deprecated in the current model, to be removed in the future. Review Biolink Model for a suitable replacement?

### warning.knowledge_graph.node.category.abstract_or_mixin

**Message:** Node has a abstract or mixin category

**Context:** node_id, identifier

**Description:** Node category is abstract or a mixin in the current model. Please consider selecting a more specific, concrete Biolink Model category?

### warning.knowledge_graph.node.id.unmapped_prefix

**Message:** Node identifier found unmapped to target categories for node

**Context:** identifier, categories

**Description:** Node CURIE identifier namespace not found among any 'id_prefix' slot values in specified categories in the validating Biolink Model version?

### warning.knowledge_graph.edge.predicate.deprecated

**Message:** Edge has deprecated predicate

**Context:** identifier

**Description:** Edge predicate is deprecated in the current model, to be removed in the future. Review Biolink Model for a suitable replacement?

### warning.knowledge_graph.edge.predicate.non_canonical

**Message:** Edge has non-canonical predicate

**Context:** edge_id, identifier

**Description:** A predicate selected for use in a knowledge graph should preferably be tagged as 'canonical' in the specified Biolink Model release?

### warning.knowledge_graph.edge.attribute.type_id.not_association_slot

**Message:** Edge has an attribute_type_id that is not an association slot

**Context:** edge_id, identifier

**Description:** Edge 'attribute_type_id' value should generally be a term defined within the biolink:association_slot hierarchy.

### warning.knowledge_graph.edge.attribute.type_id.non_biolink_prefix

**Message:** Edge has an attribute_type_id that has a non-Biolink CURIE prefix mapped to Biolink

**Context:** edge_id, identifier

**Description:** Non-Biolink CURIEs are tolerated, but not preferred, as term value for the attribute_type_id properties of edge attributes.

### warning.knowledge_graph.edge.attribute.type_id.deprecated

**Message:** Edge has a deprecated attribute_type_id

**Context:** identifier

**Description:** Edge 'attribute_type_id' is deprecated in current model, to be removed in the future. Review Biolink Model for replacement.

### warning.knowledge_graph.edge.provenance.multiple_primary

**Message:** Edge has recorded multiple 'primary' knowledge sources

**Context:** identifier, sources

**Description:** Edge attributes should record only a single primary knowledge source provenance attribute value.

### warning.knowledge_graph.edge.provenance.ara.missing

**Message:** Edge is missing ARA knowledge source provenance

**Context:** edge_id, identifier

**Description:** Edge attributes ARAs should record the Infores identifier of their knowledge source provenance with respect to ARA.

### warning.knowledge_graph.edge.provenance.kp.missing

**Message:** Edge attribute values are missing expected Knowledge Provider provenance

**Context:** edge_id, identifier, kp_source_type

**Description:** Edge attributes of ARAs and KPs should record the infores identifier of their knowledge source provenance with respect to KP.

## Information

### info.excluded

**Message:** All test case S-P-O triples from resource test location, or specific user excluded S-P-O triples

**Context:** identifier

**Description:** Check the JSON KP test edge data file for specific 'exclude_tests' directives, either global to the file, or on specific edges.

### info.compliant

**Message:** Biolink Model-compliant TRAPI Message

**Description:** Specified TRAPI message completely satisfies the target TRAPI schema and Biolink Model semantics for specified releases of these standards.

### info.input_edge.predicate.abstract

**Message:** Edge has an 'abstract' predicate

**Context:** edge_id, identifier

**Description:** Input edge data can have 'abstract' predicates, when the mode of validation is 'non-strict'.

### info.input_edge.predicate.mixin

**Message:** Edge has an 'mixin' predicate

**Context:** edge_id, identifier

**Description:** Input edge data can have 'mixin' predicates, when the mode of validation is 'non-strict'.

### info.query_graph.edge.predicate.abstract

**Message:** Edge has an 'abstract' predicate

**Context:** edge_id, identifier

**Description:** TRAPI Messages in Query Graphs can have 'abstract' predicates, when the mode of validation is 'non-strict'.

### info.query_graph.edge.predicate.mixin

**Message:** Edge has an 'mixin' predicate

**Context:** edge_id, identifier

**Description:** TRAPI Messages in Query Graphs can have 'mixin' predicates, when the mode of validation is 'non-strict'.

### info.knowledge_graph.edge.predicate.abstract

**Message:** Edge has an 'abstract' predicate

**Context:** edge_id, identifier

**Description:** TRAPI Messages in Knowledge Graphs can have 'abstract' predicates, when the mode of validation is 'non-strict'.

### info.knowledge_graph.edge.predicate.mixin

**Message:** Edge has an 'mixin' predicate

**Context:** edge_id, identifier

**Description:** TRAPI Messages in Knowledge Graphs can have 'mixin' predicates, when the mode of validation is 'non-strict'.

### info.knowledge_graph.edge.attribute.type_id.abstract

**Message:** Edge has an 'abstract' attribute_type_id

**Context:** edge_id, identifier

**Description:** TRAPI Messages in Knowledge Graphs can have 'abstract' attribute type identifiers, when the mode of validation is 'non-strict'.

### info.knowledge_graph.edge.attribute.type_id.mixin

**Message:** Edge has an 'mixin' attribute_type_id

**Context:** edge_id, identifier

**Description:** TRAPI Messages in Knowledge Graphs can have 'mixin' attribute type identifiers, when the mode of validation is 'non-strict'.

