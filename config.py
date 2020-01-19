def get_parameter():

    parameters = {
        # set path
        'path':'./',
        'data_path':'data/',
        'result_path':'results',

        # set excel data name
        'skill_data_nm':'Skill_Data.xlsx',
        'automation_data_nm':'Automation_Data.xlsx',
        'education_data_nm':'Education_Data.xlsx',

        # target years
        'target_year_list':[2008, 2019],

        # degree of automation node
        'focal_node':"4.C.3.b.2",

        # set drop node & occupation
        # node for Degree of Automation, 
        #          Required Level of Autoamtion, Related Work Experience
        #          On-Site or In-Plant Training, On-the-Job Training
        'drop_node_list':["4.C.3.b.2", "2.D.1", "3.A.1", "3.A.2", "3.A.3"], 
        'drop_occupation_list':['19-1020','45-3021'],

        # save results
        'save_job_list': True,
        'save_two_mode_job_skill_network':False,
        'save_one_mode_skill_network':False,
        'save_skill_network_table':True,
        'save_aggregated_skill_network_table':True,

        # plot results
        'plot_weight_distribution': True,
        'plot_mst':True,

    }

    return parameters