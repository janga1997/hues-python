
# coding: utf-8

import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import os
import pandasql as pdsql

pysql = lambda q: pdsql.sqldf(q, globals())


working_directory = "C:\\Users\\boa\\Documents\\Repositories_Github\\energy-hub-model-generator-aimms\\aimms_model\\energy_hub\\results"
os.chdir(working_directory)

directory = 'Generic_energy_hub_experiment_with_sizing'
experiments = next(os.walk(directory))[1]
experiments = [os.path.join(directory, var) for var in experiments]


results_capacity_heat = pd.DataFrame()
results_capacity_electricity = pd.DataFrame()
results_storage_capacity = pd.DataFrame()
results_production_elec = pd.DataFrame()
results_production_heat = pd.DataFrame()
results_total_production_elec = pd.DataFrame()
results_total_production_heat = pd.DataFrame()
results_total_cost = pd.DataFrame()
results_emissions = pd.DataFrame()


for experiment in experiments:

    ## Extract Production Capacity Data

    filename = experiment + '\\results_capacities.xlsx'
    data = pd.read_excel(filename, 'Capacity')

    data.set_index('X1')
    data.drop('head0', axis=1)
    data_elec = data.Elec.to_frame(name = 'value')
    data_elec['technology'] = data.index.values
    data_elec['experiment'] = [experiment] * len(data)

    results_capacity_electricity = results_capacity_electricity.append(data_elec)

    data_heat = data.Heat.to_frame(name = 'value')
    data_heat['technology'] = data.index.values
    data_heat['experiment'] = [experiment] * len(data)

    results_capacity_heat = results_capacity_heat.append(data_heat)

    ## Extract Storage Capacity Data

    data = pd.read_excel(filename,"Storage_capacity", header = None, index_col = None)

    if experiment == 'NetMetering':
    	data['X1'] = data['X1'].str.replace("Battery","Elec")
    	data['X1'] = data['X1'].str.replace("Hot_water_tank","Heat")
    	data = data[ data['X1'].str.contains('Net_meter') ]
    	## Have to add the grep function

    data['experiment'] = [experiment] * len(data)

    results_storage_capacity = results_storage_capacity.append(data)

    ## Extract Production Data ##

    #electricity production
    data = pd.read_excel(filename, "Output_energy_electricity")
    data_stor = pd.read_excel(filename, "Storage_output_energy")

    data_stor = data_stor.Elec.to_frame(name = 'Storage')
    data['Storage'] = data_stor

    hrs_in_wk = 7 * 24
  	wks_in_yr = np.round((8760 / (24 * 7)))

    t = pd.DataFrame()

    for i in xrange(1,wks_in_yr + 1):
    	j = [i] * hrs_in_wk
    	t = t.append(j)

    t = t.append([53] * (8760 - 8736))
    data['weeks'] = t

    data_melted = pd.melt(data, id_vars=['weeks'], value_vars=['X1'])
    data_summed = pysql('select weeks, variable, sum(value) as value from data_melted group by weeks,variable order by weeks')
    data_summed['experiment'] = [experiment] * len(data_summed)
    data_summed.columns = ["week","technology","value","experiment"]

    results_production_elec = results_production_elec.append(data_summed)

    data_total_summed = pysql('select variable, sum(value) as value from data_melted group by variable')
    data_total_summed = [experiment] * len(data_total_summed)
  	data_total_summed.columns = ["technology","value","experiment"]

  	results_total_production_elec <- results_total_production_elec.append(data_total_summed)

  	#Heat Production
  	data = pd.read_excel(filename,"Output_energy_heat")
  	data_stor = pd.read_excel(filename,"Storage_output_energy")

    data_stor = data_stor.Heat.to_frame(name = 'Storage')
    data['Storage'] = data_stor

    data_melted = pd.melt(data, id_vars=['weeks'], value_vars=['X1'])
    data_summed = pysql('select weeks, variable, sum(value) as value from data_melted group by weeks,variable order by weeks')
    data_summed['experiment'] = [experiment] * len(data_summed)
    data_summed.columns = ["week","technology","value","experiment"]

    results_production_heat = results_production_heat.append(data_summed)

    data_total_summed = pysql('select variable, sum(value) as value from data_melted group by variable')
    data_total_summed = [experiment] * len(data_total_summed)
  	data_total_summed.columns = ["technology","value","experiment"]

  	results_total_production_heat <- results_total_production_heat.append(data_total_summed)

  	##### EXTRACT COST DATA #####

	data1 = pd.read_excel(filename,"Total_cost_per_technology", header = None)
  	data2 = pd.read_excel(filename,"Total_cost_grid", header = None)
  	data3 = pd.read_excel(filename,"Total_cost_per_storage", header = None)
  	data4 = pd.read_excel(filename,"Income_via_exports", header = None)

  	data2.iloc[0,0] = data2.iloc[0,0] - data4.iloc[0,0]

  	data2b = pd.DataFrame()
  	data2b[0, 0] = 'Grid'
  	data2b[0, 1] = data2[0, 0]
  	data2b.columns = ['X1', 'X2']
  	data = pd.concat([data1, data2b, data3], axis=0)
  	data = pysql('select X1, sum(X2) as X2 from data group by X1 order by X1')
  	total_cost = sum(data.X2)

  	newcol = pd.DataFrame([experiment] * len(data))
  	data5 = pd.concat([data, newcol], axis=1)
  	data5.columns = ["technology","value",	"experiment"]
  	results_total_cost = results_total_cost.append(data5)

    total_income = data4.X1.to_frame(name = 'value')
    total_income['experiment'] = [experiment] * len(data4)

  	results_total_income = results_total_income.append(total_income)

  	#EXTRACT THE CARBON EMISSIONS
	data = pd.read_excel(filename,"Total_carbon_per_technology", header = None)

  	newcol = pd.DataFrame([experiment] * len(data))
  	emissions = pd.concat([data, newcol], axis = 1)
  	emissions.columns = ["technology", "value", "experiment"]
  	results_emissions = results_emissions.append(emissions)
