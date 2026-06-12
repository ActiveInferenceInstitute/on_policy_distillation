# GNN Example: Deterministic Graph-World Topology Sweep

## GNNSection

TemplateActiveInference_GraphWorld

## GNNVersionAndFlags

GNN v1.1

## ModelName

Deterministic Graph-World Topology Validation

## StateSpaceBlock

node[5,1,type=float]
edge[5,5,type=float]
action[2,1,type=float]
graph_policy[2,1,type=float]
goal[1,type=float]
trace_step[5,1,type=float]
goal_reached[1,type=float]

## Connections

node-edge:topology
node>action:available_actions
graph_policy>action:action_selection
action>node:controlled_transition
node>goal:goal_test
node>trace_step:trace_emission
goal>goal_reached:reachability_witness

## ActInf Ontology Annotation

node=GraphWorldState
edge=GraphWorldTopology
action=GraphWorldAction
graph_policy=GraphWorldPolicy
goal=GraphWorldGoal
trace_step=GraphWorldTrace
goal_reached=GraphWorldReachability
