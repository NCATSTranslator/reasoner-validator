# Validation Codes Dictionary

## Information

### info.excluded

**Message:** User excluded S-P-O triple '{edge_id}' or all test case S-P-O triples from resource test location.

### info.compliant

**Message:** Biolink Model-compliant TRAPI Message.

**Description:** Specified TRAPI message completely satisfies the target TRAPI schema and Biolink Model semantics for specified releases of these standards

### info.input_edge.node.category.abstract

**Message:** '{name}' is abstract.

### info.input_edge.node.category.mixin

**Message:** '{name}' is a mixin.

### info.input_edge.predicate.abstract

**Message:** '{name}' is abstract.

### info.input_edge.predicate.mixin

**Message:** '{name}' is a mixin.

### info.query_graph.node.category.abstract

**Message:** '{name}' is abstract.

### info.query_graph.node.category.mixin

**Message:** '{name}' is a mixin.

### info.query_graph.predicate.abstract

**Message:** '{name}' is abstract.

### info.query_graph.predicate.mixin

**Message:** '{name}' is a mixin.

### info.attribute_type_id.non_biolink_prefix

**Message:** Edge attribute_type_id '{attribute_type_id}' has a non-Biolink CURIE prefix mapped to Biolink.

## Warning

### warning.graph.empty

**Message:** {context} data is empty?

### warning.response.knowledge_graph.empty

**Message:** Response returned an empty Message Knowledge Graph?

### warning.response.results.empty

**Message:** Response returned empty Message.results?

### warning.input_edge.node.category.deprecated

**Message:** '{name}' is deprecated?

### warning.input_edge.node.id.unmapped_to_category

**Message:** '{node_id}' has identifiers {unmapped_ids} unmapped to the target categories: {categories}?

### warning.input_edge.predicate.deprecated

**Message:** '{name}' is deprecated?

### warning.query_graph.node.ids.unmapped_to_categories

**Message:** '{node_id}' has identifiers {unmapped_ids} unmapped to the target categories: {categories}?

### warning.knowledge_graph.node.category.deprecated

**Message:** '{name}' is deprecated?

### warning.knowledge_graph.node.unmapped_prefix

**Message:** '{node_id}' is unmapped to the target categories: {categories}?

### warning.knowledge_graph.node.id.unmapped_to_category

**Message:** {context} node identifier '{node_id}' is unmapped to '{category}'?

### warning.knowledge_graph.predicate.non_canonical

**Message:** {context} edge {edge_id} predicate '{predicate}' is non-canonical?

### warning.knowledge_graph.edge.attribute.type_id.not_association_slot

**Message:** Edge attribute_type_id '{attribute_type_id}' not a biolink:association_slot?

### warning.knowledge_graph.edge.attribute.type_id.unknown_prefix

**Message:** Edge attribute_type_id '{attribute_type_id}' has a CURIE prefix namespace unknown to Biolink!

### warning.knowledge_graph.edge.attribute.type_id.deprecated

**Message:** '{name}' is deprecated?

### warning.knowledge_graph.edge.provenance.ara.missing

**Message:** Edge is missing ARA knowledge source provenance?

### warning.knowledge_graph.edge.provenance.kp.missing

**Message:** Edge attribute values are missing expected Knowledge Provider '{kp_source}' '{kp_source_type}' provenance?

### warning.knowledge_graph.edge.provenance.missing_primary

**Message:** Edge has neither a 'primary' nor 'original' knowledge source?

## Error

### error.non_compliant

**Message:** S-P-O statement '{edge_id}' is not compliant to Biolink Model {biolink_release}

### error.trapi.validation

**Message:** TRAPI {trapi_version} Query: '{exception}'

### error.trapi.request.invalid

**Message:** {context} could not generate a valid TRAPI query request object because {reason}?

### error.trapi.response.unexpected_http_code

**Message:** TRAPI Response has an unexpected HTTP status code: '{status_code}'?

### error.trapi.response.message.empty

**Message:** Response returned an empty Message Query Graph!

### error.trapi.response.query_graph.missing

**Message:** TRAPI Message is missing its Query Graph!

### error.trapi.response.query_graph.empty

**Message:** Response returned an empty Message Query Graph?

### error.trapi.response.knowledge_graph.missing

**Message:** TRAPI Message is missing its Knowledge Graph component!

### error.trapi.response.results.missing

**Message:** TRAPI Message is missing its Results component!

### error.trapi.response.results.non_array

**Message:** Response returned a non-array Message.results!

### error.trapi.response.results.missing_bindings

**Message:** Neither the input id '{input_id}' nor resolved aliases were returned in the Result object IDs for node '{output_node_binding}' binding?

### error.input_edge.node.category.unknown

**Message:** '{name}' is unknown!

### error.input_edge.node.category.abstract

**Message:** '{name}' is abstract!

### error.input_edge.node.category.mixin

**Message:** '{name}' is a mixin!

### error.input_edge.node.id.missing

**Message:** {context} node identifier is missing!

### error.input_edge.predicate.missing

**Message:** {context} edge '{edge_id}' predicate is missing or empty!

### error.query_graph.node.category.unknown

**Message:** '{name}' is unknown!

### error.query_graph.node.category.abstract

**Message:** '{name}' is abstract!

### error.query_graph.node.category.mixin

**Message:** '{name}' is a mixin!

### error.query_graph.node.ids.not_array

**Message:** Node '{node_id}.ids' slot value is not an array!

### error.query_graph.node.categories.not_array

**Message:** Node '{node_id}.categories' slot value is not an array!

### error.query_graph.node.is_set.not_boolean

**Message:** Node '{node_id}.is_set' slot is not a boolean value!

### error.query_graph.predicate.missing

**Message:** Edge '{edge_id}' predicate is missing or empty!

### error.query_graph.predicate.not_array

**Message:** Edge '{edge_id}' predicate slot value is not an array!

### error.query_graph.predicate.empty_array

**Message:** Edge '{edge_id}' predicate slot value is an empty array!

### error.knowledge_graph.nodes.empty

**Message:** No nodes found!

### error.knowledge_graph.edges.empty

**Message:** No edges found!

### error.knowledge_graph.node.category.missing

**Message:** '{node_id}' has a missing Biolink category!

### error.knowledge_graph.node.category.unknown

**Message:** '{name}' is unknown!

### error.knowledge_graph.node.category.abstract

**Message:** '{name}' is abstract!

### error.knowledge_graph.node.category.mixin

**Message:** '{name}' is a mixin!

### error.knowledge_graph.node.id.missing

**Message:** {context} node identifier is missing!

### error.knowledge_graph.node.missing_categories

**Message:** Node '{node_id}' is missing its categories!

### error.knowledge_graph.node.ids.not_array

**Message:** Node '{node_id}.ids' slot value is not an array!

### error.knowledge_graph.node.empty_ids

**Message:** Node '{node_id}.ids' slot array is empty!

### error.knowledge_graph.node.categories.not_array

**Message:** Node '{node_id}.categories' slot value is not an array!

### error.knowledge_graph.node.empty_categories

**Message:** Node '{node_id}.categories' slot array is empty!

### error.knowledge_graph.node.is_set_not_boolean

**Message:** Node '{node_id}.is_set' slot is not a boolean value!

### error.knowledge_graph.predicate.missing

**Message:** Edge '{edge_id}' predicate is missing or empty!

### error.knowledge_graph.predicate.not_array

**Message:** Edge '{edge_id}' predicate slot value is not an array!

### error.knowledge_graph.predicate.empty_array

**Message:** Edge '{edge_id}' predicate slot value is an empty array!

### error.knowledge_graph.predicate.unknown

**Message:** Edge '{edge_id}' predicate '{predicate}' is unknown!

### error.knowledge_graph.edge.subject.missing

**Message:** Edge '{edge_id}' has a missing or empty 'subject' slot value!

### error.knowledge_graph.edge.subject.missing_from_nodes

**Message:** Edge 'subject' id '{object_id}' is missing from the nodes catalog!

### error.knowledge_graph.edge.object.missing

**Message:** Edge '{edge_id}' has a missing or empty 'object' slot value!

### error.knowledge_graph.edge.object.missing_from_nodes

**Message:** Edge 'object' id '{object_id}' is missing from the nodes catalog!

### error.knowledge_graph.edge.attribute.missing

**Message:** Edge has no 'attributes' key!

### error.knowledge_graph.edge.attribute.empty

**Message:** Edge has empty attributes!

### error.knowledge_graph.edge.attribute.not_list

**Message:** Edge attributes are not a list!

### error.knowledge_graph.edge.attribute.type_id.missing

**Message:** Edge attribute is missing its 'attribute_type_id' property!

### error.knowledge_graph.edge.attribute.type_id.empty

**Message:** Edge attribute empty 'attribute_type_id' property!

### error.knowledge_graph.edge.attribute.type_id.not_curie

**Message:** Edge attribute_type_id '{attribute_type_id}' is not a CURIE!

### error.knowledge_graph.edge.attribute.value.missing

**Message:** Edge attribute is missing its 'value' property!

### error.knowledge_graph.edge.attribute.value.empty

**Message:** Edge attribute empty 'value' property!

### error.knowledge_graph.edge.provenance.infores.missing

**Message:** Edge has provenance value '{infores}' which is not a well-formed InfoRes CURIE!

