#Subir boards de la parada 2646

stop = 2646
data_stop = final_dataframe[final_dataframe["Stop"] == 2646]
_init_stop_counters(stop)

counter_stop_2646_parameters = 0
stop_normal_boards  = 0
stop_normal_dropoffs = 0

for timeslot in timeslots:
    data_boards = data_stop[f"instances_boards_{timeslot}"].iloc[0]
    print(data_boards)
    cleaned_boards, _ = remove_outliers_mad(data_boards)
    is_normal, _, mean, std = is_normal_simplified(cleaned_boards)
    neg_bin = test_negative_binomial(cleaned_boards)
    geom    = test_geometric(cleaned_boards)

    chosen = select_by_aic(
        cleaned_boards,
        candidates_mask={'NORMAL': is_normal, 'NEGATIVE BINOMIAL': neg_bin['is_negbin'], 'GEOMETRICAL': geom['is_geometric']},
        stop=stop, timeslot=timeslot,
        dataframe=dataframe_simulation
    )
    _record('Board', stop, timeslot, chosen)

    if is_normal or neg_bin or geom:
        global_normal_boards += 1
        stop_normal_boards += 1

    counter_parameters += 1
    counter_stop_2646_parameters += 1




with open ("input_data_E01_toA.csv", "w", encoding="utf-8") as f:
    dataframe_simulation.to_csv(f, index=False)

==== same pattern in cell 8 (toB, stop 5727) ====

stop 2646 toA, slot 5: n=158
  is_normal = np.False_  (type bool)
  neg_bin   = {'is_negbin': False, 'reason': 'too few valid bins', 'statistic': 0, 'p_value': 0, 'p_hat': 0, 'r_hat': 0}
  type(neg_bin) = dict, bool(neg_bin) = True
  geom      = {'statistic': np.float64(469.3049779038333), 'p_value': np.float64(nan), 'p_hat': np.float64(0.5429553264604811), 'is_geometric': np.False_, 'df': 0}
  type(geom) = dict, bool(geom) = True
  (is_normal or neg_bin or geom) = {'is_negbin': False, 'reason': 'too few valid bins', 'statistic': 0, 'p_value': 0, 'p_hat': 0, 'r_hat': 0} -> bool True
  real verdicts: neg_bin['is_negbin'] = False, geom['is_geometric'] = False

stop 2646 toA, slot 8: n=157
  is_normal = np.True_  (type bool)
  neg_bin   = {'is_negbin': False, 'reason': 'too few valid bins', 'statistic': 0, 'p_value': 0, 'p_hat': 0, 'r_hat': 0}
  type(neg_bin) = dict, bool(neg_bin) = True
  geom      = {'statistic': np.float64(31.500029643289416), 'p_value': np.float64(nan), 'p_hat': np.float64(0.020780939774983454), 'is_geometric': np.False_, 'df': -1}
  type(geom) = dict, bool(geom) = True
  (is_normal or neg_bin or geom) = np.True_ -> bool True
  real verdicts: neg_bin['is_negbin'] = False, geom['is_geometric'] = False