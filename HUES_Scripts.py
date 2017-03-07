import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import os
import pandasql as pdsql
from ggplot import *

pysql = lambda q: pdsql.sqldf(q, globals())


working_directory = "/home/janga/ehub-modeling-tool/analysis_scripts/"
os.chdir(working_directory)

directory = 'test_data'
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

    filename = experiment + '/results_capacities.xlsx'
    data = pd.read_excel(filename, 'Capacity')

    data = pd.DataFrame.transpose(data)
    data_elec = data.Elec.to_frame(name = 'value')
    data_elec['technology'] = data.index.values
    data_elec['experiment'] = ['experiment1'] * len(data)

    results_capacity_electricity = results_capacity_electricity.append(data_elec)

    data_heat = data.Heat.to_frame(name = 'value')
    data_heat['technology'] = data.index.values
    data_heat['experiment'] = [experiment] * len(data)

    results_capacity_heat = results_capacity_heat.append(data_heat)

    ## Extract Storage Capacity Data

    filename = experiment + '/results_capacities.xlsx'
    data = pd.read_excel(filename,"Storage_capacity", header = None, index_col = None)

    if experiment == 'NetMetering':
        data[0] = data[0].str.replace("Battery","Elec")
        data[0] = data[0].str.replace("Hot_water_tank","Heat")
        data = data[ data[0].str.contains('Net_meter') ]
        ## Have to add the grep function

    data['experiment'] = [experiment] * len(data)
    data.columns = ["technology","value","experiment"]
    results_storage_capacity = results_storage_capacity.append(data)

    ## Extract Production Data ##

    #electricity production
    filename = experiment + '/results_conversion.xlsx'
    data = pd.read_excel(filename, "Output_energy_electricity")

    filename = experiment + '/results_storage.xlsx'
    data_stor = pd.read_excel(filename, "Storage_output_energy")

    data_stor = data_stor.Elec.to_frame(name = 'Storage')
    data['Storage'] = data_stor

    hrs_in_wk = 7 * 24
    wks_in_yr = int(np.round((8760 / (24 * 7))))

    t = pd.DataFrame()

    for i in range(1,wks_in_yr + 1):
        j = [i] * hrs_in_wk
        t = t.append(j)

    t = t.append([53] * (8760 - 8736))

    data = pd.concat([data] * 365)

    t = t.set_index(np.array(range(len(data))))
    data['weeks'] = t
    data['X1'] = data.index

    data_melted = pd.melt(data, id_vars=['weeks', 'X1'])
    data_summed = pysql('select weeks, variable, sum(value) as value from data_melted group by weeks,variable order by weeks')
    data_summed['experiment'] = [experiment] * len(data_summed)
    data_summed.columns = ["week","technology","value","experiment"]

    results_production_elec = results_production_elec.append(data_summed)

    data_total_summed = pysql('select variable, sum(value) as value from data_melted group by variable')
    data_total_summed['experiment'] = [experiment] * len(data_total_summed)
    data_total_summed.columns = ["technology","value","experiment"]

    results_total_production_elec = results_total_production_elec.append(data_total_summed)

      #Heat Production
    filename = experiment + '/results_conversion.xlsx'
    data = pd.read_excel(filename,"Output_energy_heat")

    filename = experiment + '/results_storage.xlsx'
    data_stor = pd.read_excel(filename,"Storage_output_energy")

    data_stor = data_stor.Heat.to_frame(name = 'Storage')
    data['Storage'] = data_stor
    data = pd.concat([data] * 365)

    data['weeks'] = t

    data['X1'] = data.index

    data_melted = pd.melt(data, id_vars=['weeks','X1'])
    data_summed = pysql('select weeks, variable, sum(value) as value from data_melted group by weeks,variable order by weeks')
    data_summed['experiment'] = [experiment] * len(data_summed)
    data_summed.columns = ["week","technology","value","experiment"]

    results_production_heat = results_production_heat.append(data_summed)

    data_total_summed = pysql('select variable, sum(value) as value from data_melted group by variable')
    data_total_summed['experiment'] = [experiment] * len(data_total_summed)
    data_total_summed.columns = ["technology","value","experiment"]

    results_total_production_heat = results_total_production_heat.append(data_total_summed)

      ##### EXTRACT COST DATA #####

    filename = experiment + '/results_costs.xlsx'
    data1 = pd.read_excel(filename,"Total_cost_per_technology", header = None)
    data2 = pd.read_excel(filename,"Total_cost_grid", header = None)
    data3 = pd.read_excel(filename,"Total_cost_per_storage", header = None)
    data4 = pd.read_excel(filename,"Income_via_exports", header = None)

    data2.iloc[0,0] = data2.iloc[0,0] - data4.iloc[0,0]

    data2b = pd.DataFrame()
    data2b = data2b.append( [['Grid', data2.iloc[0, 0]]] )
    data = pd.concat([data1, data2b, data3], axis=0)
    data.columns = ['X1', 'X2']
    data = pysql('select X1, sum(X2) as X2 from data group by X1 order by X1')
    total_cost = sum(data.X2)

    newcol = pd.DataFrame([experiment] * len(data))
    data5 = pd.concat([data, newcol], axis=1)
    data5.columns = ["technology", "value", "experiment"]
    results_total_cost = results_total_cost.append(data5)

    # total_income = data4.X1.to_frame(name = 'value')
    # total_income['experiment'] = [experiment] * len(data4)

    # results_total_income = results_total_income.append(total_income)

      #EXTRACT THE CARBON EMISSIONS
    filename = experiment + '/results_emissions.xlsx'
    data = pd.read_excel(filename,"Total_carbon_per_technology", header = None)

    newcol = pd.DataFrame([experiment] * len(data))
    emissions = pd.concat([data, newcol], axis = 1)
    emissions.columns = ["technology", "value", "experiment"]
    results_emissions = results_emissions.append(emissions)

# CREATE THE PLOTS
plot = ggplot(results_capacity_electricity, aes(x = 'experiment', weight = 'value', fill = 'technology')) + geom_bar()
plot +=labs(title="Electricity output capacity of conversion technologies",x="Experiment", y="Capacity (kW)")
plot.save("python-plots/comparison_electricity_production_capacity.png")

plot = ggplot(results_capacity_heat, aes(x = 'experiment', weight = 'value', fill = 'technology')) + geom_bar()
plot +=labs(title="Heat output capacity of conversion technologies",x="Experiment", y="Capacity (kW)")
plot.save("python-plots/comparison_heat_production_capacity.png")

plot = ggplot(results_storage_capacity, aes(x = 'experiment', weight = 'value', fill = 'technology')) + geom_bar()
plot +=labs(title="Capacity of storage technologies",x="Experiment", y="Capacity (kW)")
plot.save("python-plots/comparison_storage_capacity.png")

plot = ggplot(results_total_cost, aes(x = 'experiment', weight = 'value', fill = 'technology')) + geom_bar()
plot +=labs(title="Total cost",x="Experiment", y="Cost (CHF)")
plot.save("python-plots/comparison_total_cost.png")

# plot = ggplot(results_total_income,aes(x = 'experiment', weight = 'value')) + geom_bar()
# plot +=labs(title="Total income",x="Experiment", y="Cost (CHF)")
# plot.save("python-plots/comparison_total_income.png")

plot = ggplot(results_emissions,aes(x = 'experiment', weight = 'value', fill = 'technology')) + geom_bar()
plot +=labs(title="Total emissions",x="Experiment", y="Emissions (CO2-eq)")
plot.save("python-plots/comparison_total_emissions.png")

plot = ggplot(results_production_elec, aes(x = 'week',weight = 'value',fill = 'technology')) + geom_bar()
plot +=labs(title="Electricity supplied per technology (weekly)",x="Week", y="Energy supplied (kWh)")
plot.save("python-plots/comparison_weekly_electricity_production.png")

plot = ggplot(results_production_heat, aes(x = 'week', weight = 'value', fill = 'technology')) + geom_bar()
plot +=labs(title="Heat supplied per technology (weekly)",x="Week", y="Energy supplied (kWh)")
plot.save("python-plots/comparison_weekly_heat_production.png")

plot = ggplot(results_total_production_elec, aes(x = 'experiment', weight = 'value', fill = 'technology')) + geom_bar()
plot +=labs(title="Total electricity supplied",x="Experiment", y="Energy supplied (kWh)")
plot.save("python-plots/comparison_total_electricity_production.png")

plot = ggplot(results_total_production_heat, aes(x = 'experiment', weight = 'value', fill = 'technology')) + geom_bar()
plot +=labs(title="Total heat supplied",x="Experiment", y="Energy supplied (kWh)")
plot.save("python-plots/comparison_total_heat_production.png")
