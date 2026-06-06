# GNN Example: Full TMaze Sophisticated Inference

## GNNSection

TemplateActiveInference_SI_TMaze

## GNNVersionAndFlags

GNN v1.1

## ModelName

Full TMaze Sophisticated Inference Validation

## StateSpaceBlock

loc[5,1,type=float]
reward_loc[2,1,type=float]
obs_location[5,1,type=float]
obs_outcome[3,1,type=float]
obs_cue[3,1,type=float]
q_pi[5,1,type=float]
first_action_prob[5,1,type=float]
belief_entropy[1,type=float]
si_tree_nodes[1,type=float]

## Connections

loc>obs_location:location_likelihood
loc>obs_outcome:outcome_likelihood
reward_loc>obs_outcome:reward_dependency
loc>obs_cue:cue_likelihood
reward_loc>obs_cue:cue_validity_dependency
q_pi>first_action_prob:policy_marginalization
first_action_prob>loc:controlled_transition
q_pi>belief_entropy:planning
si_tree_nodes>q_pi:search_evidence

## ActInf Ontology Annotation

loc=HiddenState
reward_loc=HiddenState
obs_location=ObservationLikelihood
obs_outcome=ObservationLikelihood
obs_cue=ObservationLikelihood
q_pi=PolicyPosterior
first_action_prob=PolicyPosterior
belief_entropy=BeliefEntropy
si_tree_nodes=PolicyPosterior
