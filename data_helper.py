
from scipy.stats.stats import pearsonr   
import community

import networkx as nx
import numpy as np
import csv
import os

import matplotlib.pyplot as plt
from networkx.drawing.nx_agraph import graphviz_layout

def pearson_corr(G, u, v, weight='weight'):
    G_u_nbr = []
    G_v_nbr = []
       
    for nbr in set(G[u]) & set(G[v]):
        G_u_nbr.append(G.edge[u][nbr].get(weight, 1))
        G_v_nbr.append(G.edge[v][nbr].get(weight, 1))

    w = float(pearsonr(G_u_nbr ,G_v_nbr)[0])
    w = (w+1)/2
    
    return w

def mst_with_partition(distance_network, partition):

    T=nx.minimum_spanning_tree(distance_network)
        
    if partition == None:
        partition = community.best_partition(T)

    return T, partition

def distance(d):
    return float(np.sqrt((1-d['weight'])))

def distance_reverse(d):
    return float(1-d['weight']*d['weight'])    

def node_centrality(focal_node, network, skill_id_name_dict, year, partition=None):
    distance_network = network.copy()

    for u,v,d in distance_network.edges(data=True):
        d['weight']= distance(d)
    
    automation_distance = {}
    automation_value = {}
    
    for node in network.nodes():      
        if node <> focal_node:
            automation_distance[node] = distance_network.get_edge_data(focal_node,node)['weight']
            automation_value[node] = network.get_edge_data(focal_node,node)['weight']
            
    distance_network.remove_node(focal_node)
    network.remove_node(focal_node)
    
    eigen_total = nx.eigenvector_centrality(network,weight='weight')
    pagerank_total = nx.pagerank(network,weight='weight')
    
    degree_total = nx.degree(network,weight='weight')
    average_neighbor_total = nx.average_neighbor_degree(network, weight='weight')

    # distance measure
    load_total = nx.load_centrality(distance_network,normalized=True, weight='weight') #negative value error
    betweenness_total = nx.betweenness_centrality(distance_network,normalized=True, weight='weight')
    current_flow_betweenness_total = nx.current_flow_betweenness_centrality(distance_network, normalized=True, weight='weight', solver='full')
    current_flow_closeness_total = nx.current_flow_closeness_centrality(distance_network, weight='weight')
    
    # mst
    mst,partition = mst_with_partition(distance_network, partition)
    weight_mst = mst.copy()
    
    # centralities
    for u,v,d in weight_mst.edges(data=True):
        d['weight']= distance_reverse(d)

    # weight measure
    degree_mst = nx.degree(weight_mst,weight='weight')
    average_neighbor_mst = nx.average_neighbor_degree(weight_mst, weight='weight')
    
    # distance measure
    load_mst = nx.load_centrality(mst,normalized=True, weight='weight') #negative value error
    betweenness_mst = nx.betweenness_centrality(mst,normalized=True, weight='weight')
    current_flow_betweenness_mst = nx.current_flow_betweenness_centrality(mst, normalized=True, weight='weight', solver='full')
    current_flow_closeness_mst = nx.current_flow_closeness_centrality(mst, weight='weight')
    
    ##### Merge #####    
    values = []

    for node in mst.nodes():        
        values.append(partition.get(node))

    namelist = mst.nodes()
    
    for x in range(0, len(mst.node)):         
        mst.node[namelist[x]][year+'_automation_distance']= float(automation_distance[namelist[x]])
        mst.node[namelist[x]][year+'_automation_value']= float(automation_value[namelist[x]])

        mst.node[namelist[x]]['ElementID']= namelist[x]
        mst.node[namelist[x]][year+'_skill_name']= skill_id_name_dict[namelist[x]]
        mst.node[namelist[x]][year+'_skill_id']= namelist[x]
        
        mst.node[namelist[x]][year+'_community_group']= str(values[x])

        mst.node[namelist[x]][year+'_degree_total']= float(degree_total[namelist[x]])

        mst.node[namelist[x]][year+'_eigen_total']= float(eigen_total[namelist[x]])
        mst.node[namelist[x]][year+'_pagerank_total']= float(pagerank_total[namelist[x]])
        
        mst.node[namelist[x]][year+'_degree_total']= float(degree_total[namelist[x]])
        mst.node[namelist[x]][year+'_average_neighbor_total']= float(average_neighbor_total[namelist[x]])
        mst.node[namelist[x]][year+'_load_total']= float(load_total[namelist[x]])
        mst.node[namelist[x]][year+'_betweenness_total']= float(betweenness_total[namelist[x]])
        mst.node[namelist[x]][year+'_current_flow_betweenness_total']= float(current_flow_betweenness_total[namelist[x]])
        mst.node[namelist[x]][year+'_current_flow_closeness_total']= float(current_flow_closeness_total[namelist[x]])
        
        mst.node[namelist[x]][year+'_degree_mst']= float(degree_mst[namelist[x]])
        mst.node[namelist[x]][year+'_average_neighbor_mst']= float(average_neighbor_mst[namelist[x]])
        mst.node[namelist[x]][year+'_load_mst']= float(load_mst[namelist[x]])
        mst.node[namelist[x]][year+'_betweenness_mst']= float(betweenness_mst[namelist[x]])
        mst.node[namelist[x]][year+'_current_flow_betweenness_mst']= float(current_flow_betweenness_mst[namelist[x]])
        mst.node[namelist[x]][year+'_current_flow_closeness_mst']= float(current_flow_closeness_mst[namelist[x]])
        
    return mst, partition    

def group_centrality(focal_node, original_network, network, extra_network, year, partition=None):
    # compare clustering charaterstics between target and source year
    count = 0
        
    distance_network = network.copy()
        
    for u,v,d in distance_network.edges(data=True):
        d['weight']= distance(d)
    
    extra_distance_network = extra_network.copy()
    for u,v,d in extra_distance_network.edges(data=True):
        d['weight']= distance(d)
        
    distance_network.remove_node(focal_node)
    network.remove_node(focal_node)
    
    # MST
    mst_network,partition = mst_with_partition(distance_network,partition)
    mst_weight_network = mst_network.copy()

    for u,v,d in mst_weight_network.edges(data=True):
        d['weight']= distance_reverse(d)
    
    for com in set(partition.values()) :
        count = count + 1
        list_nodes = [nodes for nodes in partition.keys()
                                    if partition[nodes] == com]
                
        network_subgraph = network.subgraph(list_nodes)
        distance_network_subgraph =distance_network.subgraph(list_nodes)
        
        mst_network_subgraph = mst_network.subgraph(list_nodes)
        mst_weight_network_subgraph = mst_weight_network.subgraph(list_nodes)
                
        automation_distance_subgraph = []
        automation_value_subgraph = []
        eigen_cluster_average = []
        pagerank_cluster_average = []
        
        for node in distance_network_subgraph.nodes():
            if node <> focal_node:
                automation_distance_subgraph.append(extra_distance_network.get_edge_data(focal_node,node)['weight'])

        for node in network_subgraph.nodes():
            if node <> focal_node:
                automation_value_subgraph.append(extra_network.get_edge_data(focal_node,node)['weight'])    

        for node in network_subgraph.nodes():
            if node <> focal_node:
                eigen_cluster_average.append(original_network.node[node][year+'_eigen_total'])    
                                
        for node in network_subgraph.nodes():
            if node <> focal_node:
                pagerank_cluster_average.append(original_network.node[node][year+'_pagerank_total'])            
        
        for node in list_nodes:
            if node <> focal_node:
                original_network.node[node][year+'_automation_distance_cluster_average']= float(np.mean(automation_distance_subgraph))
                original_network.node[node][year+'_automation_value_cluster_average']= float(np.mean(automation_value_subgraph))               
                original_network.node[node][year+'_eigen_cluster_average']= float(np.mean(eigen_cluster_average))               
                original_network.node[node][year+'_pagerank_cluster_average']= float(np.mean(pagerank_cluster_average))               
                
                original_network.node[node][year+"_clustering_network_size"] = len(list_nodes)
                original_network.node[node][year+"_clustering_total_average_shortest_path_length"] = nx.average_shortest_path_length(distance_network_subgraph,weight='weight')
                original_network.node[node][year+"_clustering_total_density"] = float(nx.density(network_subgraph))
                original_network.node[node][year+"_clustering_total_average_node_connectivity"] = float(nx.average_node_connectivity(distance_network_subgraph))
                
    return original_network    

def _strip_list_attributes(G):
    for n in G.nodes(data=True):
        for k,v in n[1].iteritems():
            if type(v) is list:
                G.node[n[0]][k] = str(v)
    for e in G.edges(data=True):
        for k,v in e[2].iteritems():
            if type(v) is list:
                G.edge[e[0]][e[1]][k] = str(v)

    return G

def draw_network(mst_path, focal_node, mst, skill_id_name_dict, year, partition_base):
        
    nx.write_gexf(mst, os.path.join(mst_path, year, "skill_"+year+"_onemode_hierarchical_clustering"+"_"+focal_node+".gexf"))

    mapping = skill_id_name_dict
    mst_skillname = nx.relabel_nodes(mst,mapping)

    nx.write_gexf(mst_skillname,os.path.join(mst_path, year, "skill_"+year+"_onemode_hierarchical_clustering_partition_base_"+partition_base+"_"+focal_node+".gexf"))
    
    pos=graphviz_layout(mst,prog='twopi',args='')
    plt.figure(figsize=(8,8))
    nx.draw(mst,pos,node_size=20,alpha=0.5,node_color="blue", with_labels=False)
    plt.axis('equal')
    plt.savefig(os.path.join(mst_path, year, 'circular_'+year+"_"+focal_node+'.png'))
    
    return mst_skillname    

def to_table(path, graph):

    graph = _strip_list_attributes(graph)

    # Edge list.
    with open(path + "_edges.csv", "wb") as f:
        edges = graph.edges(data=True)
        writer = csv.writer(f, delimiter=',')
        
        # Header.
        writer.writerow(['source','target'] + [ k for k in edges[0][2].keys()])
        
        # Values.
        for e in edges:
            writer.writerow([ e[0], e[1]] + [ v for v in e[2].values()])
            
    # Node attributes.
    nodear = []
    with open(path + "_nodes.csv", "wb") as f:
        nodes = graph.nodes(data=True)
        writer = csv.writer(f, delimiter=',')
        
        # Header.
        nodear.append(['node'] + [ k for k in nodes[0][1].keys()])
        writer.writerow(['node'] + [ k for k in nodes[0][1].keys()])
        
        
        # Values.
        for n in nodes:
            nodear.append([ n[0] ] + [v for v in n[1].values()])
            writer.writerow([ n[0] ] + [v for v in n[1].values()])
    
    return nodear