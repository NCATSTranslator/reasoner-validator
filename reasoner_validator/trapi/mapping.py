from typing import Dict

from reasoner_validator import ValidationReporter


class MappingValidator(ValidationReporter):
    """
    The Mapping Validator is a wrapper class for detecting
    dangling references between nodes and edges of a graph.
    This is more of a TRAPI expectation (that all nodes and edges identifiers refer to one another)
    """
    def __init__(self):
        """
        Mapping Validator constructor.
        """
        ValidationReporter.__init__(
            self,
            prefix="Validating Knowledge Graph Node and Edge Mappings"
        )

    def check_dangling_references(self, graph: Dict):
        if not ('nodes' in graph and graph['nodes'] and 'edges' in graph and graph['edges']):
            self.report(code="warning.graph.empty", identifier="MappingValidator")
        else:
            pass


# Detect 'dangling nodes/edges' by iterating through node <-> edge mappings)
def check_node_edge_mappings(graph: Dict) -> MappingValidator:
    validator: MappingValidator = MappingValidator()
    validator.check_dangling_references(graph)
    return validator
