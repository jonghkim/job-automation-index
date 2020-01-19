#-*- coding: utf-8 -*-
from networkx.algorithms import bipartite

import networkx as nx
import pandas as pd
import csv          
import os 
import statistics
import math

import matplotlib.pyplot as plt
import data_helper

class JobAutomationIndex():
    def __init__(self, params):
        self.path = params.get('path')
        self.data_path = params.get('data_path')
        self.result_path = params.get('result_path')

        self.skill_data_nm = params.get('skill_data_nm')
        self.automation_data_nm = params.get('automation_data_nm')
        self.education_data_nm = params.get('education_data_nm')

        self.target_year_list = params.get('target_year_list')        

        # degree of automation node
        self.focal_node = params.get('focal_node')
        
        # set drop node & occupation
        self.drop_node_list = params.get('drop_node_list')
        self.drop_node_list.remove(self.focal_node)
        self.drop_occupation_list = params.get('drop_occupation_list')

        # save results
        self.save_job_list = params.get('save_job_list')
        self.save_two_mode_job_skill_network = params.get('save_two_mode_job_skill_network')
        self.save_one_mode_skill_network = params.get('save_one_mode_skill_network')
        self.save_skill_network_table = params.get('save_skill_network_table')
        self.save_aggregated_skill_network_table = params.get('save_aggregated_skill_network_table')

        # plot option
        self.plot_weight_distribution = params.get('plot_weight_distribution')
        self.plot_mst = params.get('plot_mst')

        # get skill dataframe
        self.skill_df = self.get_skill_df
        self.job_id = self.skill_df['Occupation'].unique().tolist()

        self.skill_id_name_dict = {}
        name = self.skill_df['ElementName'].tolist()
        skill = self.skill_df['ElementID'].tolist()
        for nm, sk in zip(name, skill):
            self.skill_id_name_dict[sk] = nm        

        # generate result paths
        for target_year in self.target_year_list:
            if not os.path.exists(os.path.join(self.path,self.result_path,str(target_year))):
                os.makedirs(os.path.join(self.path,self.result_path,str(target_year)))

    @property
    def get_skill_df(self):
        skill_df = pd.read_excel(os.path.join(self.data_path, self.skill_data_nm))
        automation_df = pd.read_excel(os.path.join(self.data_path, self.automation_data_nm))
        education_df = pd.read_excel(os.path.join(self.data_path, self.education_data_nm))

        skill_df = skill_df.append(automation_df)
        skill_df = skill_df.append(education_df)
        
        skill_df = skill_df[~skill_df["ElementID"].isin(self.drop_node_list)]

        for drop_occupation in self.drop_occupation_list:
            skill_df = skill_df[skill_df['Occupation']!=drop_occupation]
        
        return skill_df

    def create_job_node(self, skill_df):

        job_node = []
        job_skill_df = pd.DataFrame(columns = skill_df.columns)
        grouped_job =  skill_df.groupby('Occupation')

        for name, group in grouped_job:
            job_node.append(name)
            job_skill_df = job_skill_df.append(group)

        print("- Number of Job {}".format(len(job_node)))

        if self.save_job_list ==True:
            jobs = pd.DataFrame()
            jobs['ONETSOCCode'] = job_node
            jobs.to_csv(os.path.join(self.path, self.result_path,"job_list.csv"))
        
        return job_node, job_skill_df

    def create_skill_node(self, job_skill_df):
        skill_node = []
        weight_targets = {}

        job_skill_grouped_df = job_skill_df.groupby('ElementID')

        skill_node = job_skill_grouped_df.groups.keys()

        print("- Number of Skills {}".format(len(skill_node)))

        # Normalize Skill Importance
        for target_year in self.target_year_list:    
            print("- Normalizing {} year skill importance".format(target_year))
            weight = []            
            for name, group in job_skill_grouped_df:
                group["Value"+str(target_year)] = (group["Value"+str(target_year)] - group["Value"+str(target_year)].mean()) / (group["Value"+str(target_year)].std())

                for i,row in group.iterrows():
                    weight.extend([(row['Occupation'],row['ElementID'],row["Value"+str(target_year)])])    

            weight_targets[target_year] = weight              
        
        for target_year in self.target_year_list:    
            print("- Num of weights at {} : {}".format(str(target_year), len(weight_targets[target_year])))
        
        return skill_node, weight_targets

    def create_job_skill_network(self, job_node, skill_node, weight_targets):

        skill_network_targets = {}

        for target_year in self.target_year_list:
            skill_network = nx.Graph()
            skill_network.add_nodes_from(job_node, bipartite=0) # Add the node attribute "bipartite"
            skill_network.add_nodes_from(skill_node, bipartite=1)
            skill_network.add_weighted_edges_from(weight_targets[target_year])
            
            skill_network_targets[target_year] = skill_network
            
            # To Save Skill Network
            if self.save_two_mode_job_skill_network ==True:
                nx.write_gexf(skill_network,os.path.join(self.path,self.result_path,target_year,"twomode_"+target_year+".gexf"))
            
        # Job node - target
        skill_network_job_node = set(n for n,d in skill_network.nodes(data=True) if d['bipartite']==0)
        # Skill node - target
        skill_network_skill_node = set(skill_network) - skill_network_job_node

        return skill_network_targets, skill_network_job_node, skill_network_skill_node

    def project_one_mode_skill_network(self, skill_network_targets, skill_network_skill_node):
        skill_onemode_targets = {}

        for target_year in self.target_year_list:
            skill_onemode = bipartite.generic_weighted_projected_graph(skill_network_targets[target_year], 
                                                                    skill_network_skill_node, weight_function=data_helper.pearson_corr)
            
            skill_onemode_targets[target_year] = skill_onemode

            if self.save_one_mode_skill_network == True:
                nx.write_gexf(skill_onemode,os.path.join(self.path, self.result_path,target_year,"skill_onemode_"+target_year+".gexf"))

        if self.plot_weight_distribution == True:
            for target_year in self.target_year_list:
                edges = []
                for edge in skill_onemode_targets[target_year].edges(data=True): edges.append(edge[2]['weight'])

                n, bins, patches = plt.hist(edges, 100, normed=0, facecolor='g', alpha=0.75)
                plt.tight_layout()

                plt.xlabel('Degree')
                plt.ylabel('Count')
                plt.title('Histogram of {} Skill degree distribution'.format(target_year))
                plt.grid(True)
                plt.savefig(os.path.join(self.path,self.result_path,str(target_year),'weight_dist_'+str(target_year)+'.png'))
                plt.close()

        return skill_onemode_targets
 
    def mst_based_clustering(self, skill_onemode_targets):

        print("- Minimal Spanning Tree")
        partitions = {}        
        for target_year in self.target_year_list:
            print("  Target Year: {}".format(target_year))
            skill_onemode = skill_onemode_targets[target_year]

            # Partition by source
            cp_skill_onemode = skill_onemode.copy()
            
            mst, partition = data_helper.node_centrality(self.focal_node, cp_skill_onemode, self.skill_id_name_dict, str(target_year), None)
            partitions[target_year] = partition

        print("- Calculate Centrality")
        mst_targets = {}
        for target_year in self.target_year_list:
            for partition_year in self.target_year_list:
                print("  Target Year: {} Particion Year: {}".format(target_year, partition_year))
                skill_onemode = skill_onemode_targets[target_year]

                # Partition by source
                cp_skill_onemode = skill_onemode.copy()

                mst, partition = data_helper.node_centrality(self.focal_node, cp_skill_onemode, self.skill_id_name_dict, str(target_year), partitions[partition_year])

                cp_skill_onemode = skill_onemode.copy()
                cp_skill_onemode2 = skill_onemode.copy()

                mst = data_helper.group_centrality(self.focal_node, mst, cp_skill_onemode, cp_skill_onemode2, str(target_year), partitions[partition_year])

                if self.plot_mst == True:
                    mst_path = os.path.join(self.path, self.result_path)
                    mst_skillname = data_helper.draw_network(mst_path, self.focal_node, mst, self.skill_id_name_dict, str(target_year), str(partition_year))

                mst_targets[str(target_year)+"_partition_base_"+str(partition_year)] = mst_skillname

        return mst_targets

    def clustering_to_table(self, mst_targets):
        node_list_targets = {}
        for target_year in self.target_year_list:    
            for partition_year in self.target_year_list:    
                cluster_path = os.path.join(self.path, self.result_path, str(target_year), "skill_"+str(target_year)+"_onemode_hierarchical_clustering_std_skillname_partition_base_"+str(partition_year)+"_"+self.focal_node)
                node_list = data_helper.to_table(cluster_path, mst_targets[str(target_year)+"_partition_base_"+str(partition_year)])
                node_list_targets[str(target_year)+"_partition_base_"+str(partition_year)] = node_list        

        for partition_year in self.target_year_list: 
            target_year_dfs = []
            for target_year in self.target_year_list:   
                target_year_info = node_list_targets[str(target_year)+"_partition_base_"+str(partition_year)]
                target_year_info_df = pd.DataFrame(target_year_info[1:],columns = node_list_targets[str(target_year)+"_partition_base_"+str(partition_year)][0])
                target_year_dfs.append(target_year_info_df)
                
            node_merged = reduce(lambda x, y: pd.merge(x, y, on = ['node','ElementID'], how='inner'), target_year_dfs)
            if self.save_skill_network_table == True:
                node_merged.to_csv(os.path.join(self.path,self.result_path, "skill_one_mode_network_merged_partition_base_"+str(partition_year)+"_"+self.focal_node+".csv"))

        for partition_year in self.target_year_list:    
            for target_year in self.target_year_list:    
                target_year_info = node_list_targets[str(target_year)+"_partition_base_"+str(partition_year)]
                target_year_info_df = pd.DataFrame(target_year_info[1:],columns = node_list_targets[str(target_year)+"_partition_base_"+str(partition_year)][0])
                        
                target_year_info_df = target_year_info_df[[str(target_year)+'_community_group','node',
                                                        str(target_year)+'_automation_value_cluster_average',
                                                        str(target_year)+'_eigen_cluster_average',
                                                        str(target_year)+'_pagerank_cluster_average',
                                                        str(target_year)+'_automation_value',
                                                        str(target_year)+'_eigen_total',
                                                        str(target_year)+'_pagerank_total']]

                target_year_info_df = target_year_info_df.sort_values(str(target_year)+'_community_group')

                cluster_target_collapse = []

                if self.save_aggregated_skill_network_table == True:
                    f1 = open(os.path.join(self.path,self.result_path, str(target_year), str(target_year)+"_clsuter_level_collapse_partition_base_"+str(partition_year)+"_"+self.focal_node+".csv"), 'wb')

                    for x in range(0,target_year_info_df.shape[0]-1):
                        if target_year_info_df.iloc[x][str(target_year)+"_community_group"] == target_year_info_df.iloc[x+1][str(target_year)+"_community_group"]:
                            cluster_target_collapse.extend(list(target_year_info_df.iloc[x]))

                        if target_year_info_df.iloc[x][str(target_year)+"_community_group"] <> target_year_info_df.iloc[x+1][str(target_year)+"_community_group"]:
                            cluster_target_collapse.extend(list(target_year_info_df.iloc[x]))
                            writer = csv.writer(f1)
                            writer.writerow(cluster_target_collapse)
                            cluster_target_collapse = []

                        if x == target_year_info_df.shape[0]-2:
                            cluster_target_collapse.extend(list(target_year_info_df.iloc[x+1]))
                            writer = csv.writer(f1)
                            writer.writerow(cluster_target_collapse)
                            cluster_target_collapse = [] 

                    f1.close()  

    def run(self):
        print("***** Create Job Skill Node *****")
        job_node, job_skill_df = self.create_job_node(self.skill_df)
        skill_node, weight_targets = self.create_skill_node(job_skill_df)

        print("\n***** Create Job Skill Two Mode Network *****")
        skill_network_targets, _, skill_network_skill_node = self.create_job_skill_network(job_node, skill_node, weight_targets)

        print("\n***** Create Skill One Mode Network *****")
        skill_onemode_targets = self.project_one_mode_skill_network(skill_network_targets, skill_network_skill_node)

        print("\n***** Clustering with MST *****")
        mst_targets = self.mst_based_clustering(skill_onemode_targets)
        self.clustering_to_table(mst_targets)

if __name__ == "__main__":
    print("## Job Automation Index ##")

    from config import get_parameter
    parameter = get_parameter()

    job_auto_index = JobAutomationIndex(parameter)
    job_auto_index.run()
