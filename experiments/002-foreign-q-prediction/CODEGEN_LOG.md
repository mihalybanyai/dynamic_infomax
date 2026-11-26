# Codegen log — 002-foreign-q-prediction

Implementation of `specs/002-foreign-q-prediction.md` §4 against `tests/test_002_*.py`,
per `workflows/implement-spec.md`. Design decisions are in
`docs/002-foreign-q-prediction/README.md`. Started 2026-11-25.

## File status

| File | Status | Last-passing commit |
|------|--------|---------------------|
| src/infomax/models.py | pending-tests | (none yet) |
| src/infomax/mixture.py | pending-tests | (none yet) |
| src/infomax/quadrature.py | pending-tests | (none yet) |
| src/infomax/priors002.py | pending-tests | (none yet) |
| src/infomax/ba.py | pending-tests | (none yet) |
| src/infomax/capacity.py | pending-tests | (none yet) |
| src/infomax/pstar.py | pending-tests | (none yet) |
| src/infomax/plat.py | pending-tests | (none yet) |
| src/infomax/pproj.py | pending-tests | (none yet) |
| src/infomax/pref.py | pending-tests | (none yet) |
| src/infomax/plognormal.py | pending-tests | (none yet) |
| src/infomax/jeffreys.py | pending-tests | (none yet) |
| src/infomax/sampled.py | pending-tests | (none yet) |
| src/infomax/qfamily.py | pending-tests | (none yet) |
| src/infomax/score.py | pending-tests | (none yet) |
| src/infomax/diagnostics.py | pending-tests | (none yet) |
| tests/fixtures/atomicpriors/generate.jl | pending-tests | (none yet) |
| experiments/002-foreign-q-prediction/run.py | pending | (none yet) |

## Test status

Outcomes of the first runs, against uncommitted code (2026-11-25); the per-test commit
hashes are filled at stage 3, after the eye test is approved.

| Test | Cases | Status | Last-passing commit |
|---|---|---|---|
| `test_002_diagnostics.py::test_t21a_mass_bound` | 2 | passing | (none yet) |
| `test_002_diagnostics.py::test_t21a_mass_bound_in_the_hypercone` | 3 | not-yet-run | (none yet) |
| `test_002_diagnostics.py::test_t21a_mass_near_is_a_sum_of_weights` | 1 | passing (precondition fixed; Testing notes) | (none yet) |
| `test_002_diagnostics.py::test_t21b_insurance_inequality` | 4 | not-yet-run | (none yet) |
| `test_002_diagnostics.py::test_t21c_full_loss_exceeds_the_relevant_datum_divergence` | 2 | passing | (none yet) |
| `test_002_diagnostics.py::test_t21c_jeffreys_cone_loss_formula` | 2 | passing | (none yet) |
| `test_002_diagnostics.py::test_t22a_moment_matched_predictive_is_as_defined` | 1 | passing | (none yet) |
| `test_002_diagnostics.py::test_t22a_split_on_every_row` | 2 | not-yet-run | (none yet) |
| `test_002_diagnostics.py::test_t22a_split_terms_vanish_on_the_diagonal` | 1 | passing | (none yet) |
| `test_002_diagnostics.py::test_t22b_beyond_cap_label` | 4 | passing | (none yet) |
| `test_002_diagnostics.py::test_t22b_capacity_gap_and_capacity` | 1 | passing | (none yet) |
| `test_002_diagnostics.py::test_t22c_covered_fraction_matches_the_interval` | 2 | not-yet-run | (none yet) |
| `test_002_diagnostics.py::test_t22d_joint_width_in_the_cone_is_closed_form` | 1 | passing | (none yet) |
| `test_002_diagnostics.py::test_t22d_joint_width_ratio_is_recorded` | 1 | passing | (none yet) |
| `test_002_diagnostics.py::test_t22e_failure_map_coordinates` | 1 | passing | (none yet) |
| `test_002_diagnostics.py::test_t22f_budget_tuning_pairs_and_ranking` | 1 | passing | (none yet) |
| `test_002_diagnostics.py::test_t22f_exchange_and_the_cast_present_at_every_D` | 1 | passing | (none yet) |
| `test_002_diagnostics.py::test_t22f_gap_to_jeffreys_and_to_the_privileged_priors` | 1 | passing | (none yet) |
| `test_002_diagnostics.py::test_t22f_relatives_world` | 1 | passing | (none yet) |
| `test_002_diagnostics.py::test_t5_gaussian_kl_split_matches_numeric_kl` | 1 | passing | (none yet) |
| `test_002_diagnostics.py::test_t5_gaussian_kl_split_vanishes_when_matched` | 1 | passing | (none yet) |
| `test_002_diagnostics.py::test_t5_pure_shift_and_pure_spread` | 1 | passing | (none yet) |
| `test_002_diagnostics.py::test_t6_hypercone_jeffreys_deviation` | 3 | passing | (none yet) |
| `test_002_diagnostics.py::test_t6_hypercone_jeffreys_mode_is_the_exact_root` | 3 | passing | (none yet) |
| `test_002_models.py::test_t13a_metric_matches_finite_differences` | 5 | passing | (none yet) |
| `test_002_models.py::test_t13a_metric_with_curvature_matches_finite_differences` | 2 | passing | (none yet) |
| `test_002_models.py::test_t13b_exp_decay_map_known_values` | 1 | passing | (none yet) |
| `test_002_models.py::test_t13b_exp_decay_symmetry_and_ordered_theta` | 1 | passing | (none yet) |
| `test_002_models.py::test_t13b_matched_box_is_the_window` | 1 | passing | (none yet) |
| `test_002_models.py::test_t13c_constant_cross_section_has_flat_volume` | 1 | passing | (none yet) |
| `test_002_models.py::test_t13c_hypercone_covolume_and_widths` | 6 | passing | (none yet) |
| `test_002_models.py::test_t13d_curvature_knob_through_the_model` | 2 | passing | (none yet) |
| `test_002_models.py::test_t13d_curvature_off_is_identity` | 1 | passing | (none yet) |
| `test_002_models.py::test_t13d_vertex_warp` | 2 | passing | (none yet) |
| `test_002_natures.py::test_t14a_round_robin_draws_come_from_the_prior` | 1 | passing | (none yet) |
| `test_002_natures.py::test_t14a_samplers_match_their_densities` | 7 | passing (closed-form reference for product laws; Testing notes) | (none yet) |
| `test_002_natures.py::test_t14b_nested_cone_laws` | 2 | passing | (none yet) |
| `test_002_natures.py::test_t14c_agent_fixes_ignored_coordinates_at_centre` | 1 | passing | (none yet) |
| `test_002_natures.py::test_t14d_few_rates_share_one_rate_in_the_window` | 1 | passing | (none yet) |
| `test_002_natures.py::test_t14e_interior_nature_is_truncated_normal` | 1 | passing | (none yet) |
| `test_002_natures.py::test_t14e_vertex_nature_is_uniform_by_area` | 1 | passing | (none yet) |
| `test_002_natures.py::test_t14e_vertex_nature_lies_on_faces_near_v` | 1 | passing | (none yet) |
| `test_002_natures.py::test_t14f_qbar_is_the_average_of_the_rows` | 1 | passing | (none yet) |
| `test_002_natures.py::test_t14g_nature_marginals_match_brute_force` | 4 | passing | (none yet) |
| `test_002_natures.py::test_t14h_submodel_floor_is_the_projection_loss` | 1 | passing | (none yet) |
| `test_002_natures.py::test_t14i_nested_cell_is_one_nature_for_every_agent` | 1 | passing | (none yet) |
| `test_002_pipeline.py::test_t10_seed_determinism` | 1 | passing | (none yet) |
| `test_002_pipeline.py::test_t2_pipeline_pJ_equals_pU` | 4 | passing | (none yet) |
| `test_002_priors.py::test_t11_nml_normaliser_in_the_1d_cone` | 1 | passing | (none yet) |
| `test_002_priors.py::test_t11_pproj_cloud_is_slab_and_spike_in_the_1d_cone` | 1 | passing | (none yet) |
| `test_002_priors.py::test_t11_pproj_information_below_capacity` | 4 | passing | (none yet) |
| `test_002_priors.py::test_t11_pproj_projection_recovers_mle` | 4 | passing | (none yet) |
| `test_002_priors.py::test_t11_projection_maps_outside_data_to_the_endpoints` | 1 | passing | (none yet) |
| `test_002_priors.py::test_t11_projection_of_data_beyond_the_manifold_lands_on_a_face` | 1 | passing | (none yet) |
| `test_002_priors.py::test_t15a_cone_schur_complement` | 2 | passing | (none yet) |
| `test_002_priors.py::test_t15b_c_cone_pref_is_uniform` | 2 | passing | (none yet) |
| `test_002_priors.py::test_t15d_exp_decay_pref_matches_the_berger_bernardo_formula` | 2 | passing | (none yet) |
| `test_002_priors.py::test_t15d_exp_decay_rankings_normalise_and_differ` | 1 | passing | (none yet) |
| `test_002_priors.py::test_t15e_stiffest_ranking_ignores_transversal` | 1 | passing | (none yet) |
| `test_002_priors.py::test_t15f_cone_pref_with_curvature` | 1 | passing | (none yet) |
| `test_002_priors.py::test_t16a_b_plat_conditional_equalizer_and_bounds` | 3 | passing (DD-S1 tolerance at the cheap cell; Testing notes) | (none yet) |
| `test_002_priors.py::test_t16c_plat_at_zero_budget_is_pstar` | 2 | passing | (none yet) |
| `test_002_priors.py::test_t16d_conditional_capacity_is_a_difference_of_informations` | 2 | passing | (none yet) |
| `test_002_priors.py::test_t16e_gaussian_plat_matches_a_direct_maximisation` | 4 | passing | (none yet) |
| `test_002_priors.py::test_t19a_b_misbudgeted_is_pstar_of_its_budget` | 1 | passing | (none yet) |
| `test_002_priors.py::test_t19c_misbudget_worst_case_exceeds_capacity` | 1 | passing | (none yet) |
| `test_002_priors.py::test_t23_lognormal_is_as_defined` | 1 | passing | (none yet) |
| `test_002_priors.py::test_t23_tuned_lognormal_information_order` | 2 | passing | (none yet) |
| `test_002_priors.py::test_t23_tuned_lognormal_is_a_local_maximum` | 2 | passing | (none yet) |
| `test_002_priors.py::test_t3_pstar_equalizer` | 1 | passing | (none yet) |
| `test_002_priors.py::test_t4_jeffreys_cone_marginal` | 1 | passing | (none yet) |
| `test_002_priors.py::test_t4_sampled_jeffreys_normaliser_matches_brute_force` | 2 | passing | (none yet) |
| `test_002_priors.py::test_t4_pointwise_marginals_agree` | 1 | passing | (none yet) |
| `test_002_priors.py::test_t4_jeffreys_normaliser_converges_on_whole_manifold` | 1 | passing | (none yet) |
| `test_002_priors.py::test_t4_jeffreys_normaliser_matches_an_independent_quadrature` | 1 | passing | (none yet) |
| `test_002_priors.py::test_t4_jeffreys_normalises` | 2 | passing | (none yet) |
| `test_002_priors.py::test_t4_uniform_density_is_absolute` | 1 | passing | (none yet) |
| `test_002_priors.py::test_t7b_pstar_method_agreement` | 1 | passing (the adaptive pool) | (none yet) |
| `test_002_references.py::test_t12a_exp_decay_map_and_metric` | 1 | passing | (none yet) |
| `test_002_references.py::test_t12b_pstar_matches_atomicpriors` | 2 | passing | (none yet) |
| `test_002_references.py::test_t12c_capacity_at_reduced_noise` | 2 | passing | (none yet) |
| `test_002_references.py::test_t12d_mutual_information_of_a_fixed_prior` | 1 | passing | (none yet) |
| `test_002_references.py::test_t12e_pproj_port_matches_transtrum` | 1 | passing | (none yet) |
| `test_002_references.py::test_t12f_atomic_path_not_below_atomicpriors` | 2 | passing | (none yet) |
| `test_002_references.py::test_t18_plat_matches_tanaka` | 2 | passing | (none yet) |
| `test_002_references.py::test_t9_am_prior_side_dominance` | 4 | not-yet-run | (none yet) |
| `test_002_scores.py::test_t17_one_step_score` | 1 | passing | (none yet) |
| `test_002_scores.py::test_t17c_predictive_is_the_ratio_of_marginals` | 2 | passing | (none yet) |
| `test_002_scores.py::test_t17d_cumulative_score_depends_on_sigma_over_root_N_only` | 1 | passing | (none yet) |
| `test_002_scores.py::test_t1_redundancy_decomposition` | 1 | passing | (none yet) |
| `test_002_scores.py::test_t1b_score_matches_quadrature_in_the_1d_cone` | 1 | passing | (none yet) |
| `test_002_scores.py::test_t1c_mcse_is_the_standard_error_of_the_draws` | 1 | passing | (none yet) |
| `test_002_scores.py::test_t1d_floor_and_mismatch_errors_match_their_spread` | 1 | not-yet-run | (none yet) |
| `test_002_scores.py::test_t1e_gap_error_comes_from_per_draw_differences` | 1 | passing | (none yet) |
| `test_002_scores.py::test_t20_round_robin_mismatches_are_non_negative` | 1 | passing | (none yet) |
| `test_002_scores.py::test_t7a_continuous_quadrature_matches_a_fine_atom_sum` | 3 | passing (reference grid fixed; Testing notes) | (none yet) |
| `test_002_scores.py::test_t7a_discrete_marginal_is_the_atom_sum` | 1 | passing | (none yet) |
| `test_002_scores.py::test_t7a_discrete_predictive_is_the_atom_sum` | 1 | passing | (none yet) |
| `test_002_scores.py::test_t7a_tapered_cone_marginal_matches_brute_force` | 4 | passing | (none yet) |
| `test_002_scores.py::test_t7c_budget_through_the_noise` | 1 | passing | (none yet) |
| `test_002_scores.py::test_t7c_two_fold_divergence_by_explicit_monte_carlo` | 1 | passing | (none yet) |
| `test_002_scores.py::test_t8_floors_and_matched_prior` | 1 | passing | (none yet) |
| `test_002_scores.py::test_t8_floors_on_every_row` | 2 | not-yet-run | (none yet) |
| `test_002_scores.py::test_t8_qbar_wins_the_row_average_and_splits_the_mean` | 1 | passing | (none yet) |

## Eye test status

| Eye test | Status | Figure path |
|----------|--------|-------------|
| A&M Fig. 5, default run `D <= 4` (band for `B`, §5.3 as revised) | passed (MB, 2026-11-25) | tests/figures/002_foreign_q_prediction/eyetest_am_fig5.png |
| A&M Fig. 5, extended run `D in {5, 7, 11}` | partial: `D = 5, 7` on the atomic path with sampled `p_J` from `D = 4` (2026-11-26; 814 s and 963 s). `D ≤ 5` approved by MB on the old Jeffreys grid; the redraw awaits review. At `D = 7`, `I(p_J)` is 0.19 bits below A&M (handoff, thread 5). `D = 11` not run | tests/figures/002_foreign_q_prediction/eyetest_am_fig5.png |
| Komaki Fig. 1 (binomial `p_lat`) | passed (MB, 2026-11-25) | tests/figures/002_foreign_q_prediction/eyetest_komaki_fig1.png |
