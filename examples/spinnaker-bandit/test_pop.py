import spynnaker8 as p
# from spynnaker.pyNN.connections. \
#     spynnaker_live_spikes_connection import SpynnakerLiveSpikesConnection
# from spinn_front_end_common.utilities.globals_variables import get_simulator
#
# import pylab
# from spynnaker.pyNN.spynnaker_external_device_plugin_manager import \
#     SpynnakerExternalDevicePluginManager as ex
import sys, os
import time
import socket
import numpy as np
from spinn_bandit.python_models.bandit import Bandit
from python_models.pendulum import Pendulum
from rank_inverted_pendulum.python_models.rank_pendulum import Rank_Pendulum
from double_inverted_pendulum.python_models.double_pendulum import DoublePendulum
import spinn_gym as gym
from spinn_arm.python_models.arm import Arm
# from spinn_breakout import Breakout
import math
import itertools
import sys
import termios
import contextlib
from copy import deepcopy
import operator
from spinn_front_end_common.utilities.globals_variables import get_simulator
import traceback
import math
from methods.networks import motif_population
import traceback
import csv
import threading
import subprocess
import pathos.multiprocessing
from spinn_front_end_common.utilities import globals_variables
import argparse
from ast import literal_eval


def split_ex_in(connections):
    excite = []
    inhib = []
    for conn in connections:
        if conn[2] > 0:
            excite.append(conn)
        else:
            inhib.append(conn)
    for conn in inhib:
        conn[2] *= -1
    return excite, inhib

def split_plastic(connections):
    plastic = []
    non_plastic = []
    for conn in connections:
        if conn[4] == 'plastic':
            plastic.append([conn[0], conn[1], conn[2], conn[3]])
        else:
            non_plastic.append([conn[0], conn[1], conn[2], conn[3]])
    return plastic, non_plastic

def connect_to_arms(pre_pop, from_list, arms, r_type, plastic, stdp_model):
    arm_conn_list = []
    for i in range(len(arms)):
        arm_conn_list.append([])
    for conn in from_list:
        arm_conn_list[conn[1]].append((conn[0], 0, conn[2], conn[3]))
        # print "out:", conn[1]
        # if conn[1] == 2:
        #     print '\nit is possible\n'
    for i in range(len(arms)):
        if len(arm_conn_list[i]) != 0:
            if plastic:
                p.Projection(pre_pop, arms[i], p.FromListConnector(arm_conn_list[i]),
                             receptor_type=r_type, synapse_type=stdp_model)
            else:
                p.Projection(pre_pop, arms[i], p.FromListConnector(arm_conn_list[i]),
                             receptor_type=r_type)

def get_scores(game_pop, simulator):
    g_vertex = game_pop._vertex
    scores = g_vertex.get_data(
        'score', simulator.no_machine_time_steps, simulator.placements,
        simulator.graph_mapper, simulator.buffer_manager, simulator.machine_time_step)
    return scores.tolist()

def connect_genes_to_fromlist(number_of_nodes, connections, nodes):
    i2i_ex = []
    i2i_in = []
    i2h_ex = []
    i2h_in = []
    i2o_ex = []
    i2o_in = []
    h2i_ex = []
    h2i_in = []
    h2h_ex = []
    h2h_in = []
    h2o_ex = []
    h2o_in = []
    o2i_ex = []
    o2i_in = []
    o2h_ex = []
    o2h_in = []
    o2o_ex = []
    o2o_in = []

    ex_or_in = {}
    translator = []
    i = 0
    for node in nodes:
        # translator.append([literal_eval(node), i])
        ex_or_in[node] = [nodes[node].activation, i]
        # print(node, ': ', ex_or_in[node])
        i += 1

    #individual: Tuples of (innov, from, to, weight, enabled)
    # if number_of_nodes > 4:
    #     print('hold it here')

    hidden_size = number_of_nodes - output_size

    for conn in connections:
        c = connections[conn]
        connect_weight = c.weight
        if c.enabled:
            # print('0:', c.key[0], '\t1:', c.key[1])
            if c.key[0] < 0:
                if c.key[1] < 0:
                    i2i_ex.append((c.key[0]+input_size, c.key[1]+input_size, connect_weight, delay))
                elif c.key[1] < output_size:
                    i2o_ex.append((c.key[0]+input_size, c.key[1], connect_weight, delay))
                elif ex_or_in[c.key[1]][1] < hidden_size + output_size:
                    i2h_ex.append((c.key[0]+input_size, ex_or_in[c.key[1]][1]-output_size, connect_weight, delay))
                else:
                    print("shit broke")
            elif c.key[0] < output_size:
                if c.key[1] < 0:
                    if ex_or_in[c.key[0]][0] == 'excitatory':
                        o2i_ex.append((c.key[0], c.key[1]+input_size, connect_weight, delay))
                    else:
                        o2i_in.append((c.key[0], c.key[1]+input_size, connect_weight, delay))
                elif c.key[1] < output_size:
                    if ex_or_in[c.key[0]][0] == 'excitatory':
                        o2o_ex.append((c.key[0], c.key[1], connect_weight, delay))
                    else:
                        o2o_in.append((c.key[0], c.key[1], connect_weight, delay))
                elif ex_or_in[c.key[1]][1] < hidden_size + output_size:
                    if ex_or_in[c.key[0]][0] == 'excitatory':
                        o2h_ex.append((c.key[0], ex_or_in[c.key[1]][1]-output_size, connect_weight, delay))
                    else:
                        o2h_in.append((c.key[0], ex_or_in[c.key[1]][1]-output_size, connect_weight, delay))
                else:
                    print("shit broke")
            elif ex_or_in[c.key[0]][1] < hidden_size + output_size:
                if c.key[1] < 0:
                    if ex_or_in[c.key[0]][0] == 'excitatory':
                        h2i_ex.append((ex_or_in[c.key[0]][1]-output_size, c.key[1]+input_size, connect_weight, delay))
                    else:
                        h2i_in.append((ex_or_in[c.key[0]][1]-output_size, c.key[1]+input_size, connect_weight, delay))
                elif c.key[1] < output_size:
                    if ex_or_in[c.key[0]][0] == 'excitatory':
                        h2o_ex.append((ex_or_in[c.key[0]][1]-output_size, c.key[1], connect_weight, delay))
                    else:
                        h2o_in.append((ex_or_in[c.key[0]][1]-output_size, c.key[1], connect_weight, delay))
                elif ex_or_in[c.key[1]][1] < hidden_size + output_size:
                    if ex_or_in[c.key[0]][0] == 'excitatory':
                        h2h_ex.append((ex_or_in[c.key[0]][1]-output_size, ex_or_in[c.key[1]][1]-output_size, connect_weight, delay))
                    else:
                        h2h_in.append((ex_or_in[c.key[0]][1]-output_size, ex_or_in[c.key[1]][1]-output_size, connect_weight, delay))
                else:
                    print("shit broke")
            else:
                print("shit broke")


    return i2i_ex, i2h_ex, i2o_ex, h2i_ex, h2h_ex, h2o_ex, o2i_ex, o2h_ex, o2o_ex, i2i_in, i2h_in, i2o_in, h2i_in, h2h_in, h2o_in, o2i_in, o2h_in, o2o_in

def parse_connections(from_list):
    if parse_conn:
        new_list = []
        for conn in from_list:
            new_conn = deepcopy(conn)
            # conn[2] = 0.1
            new_list.append((conn[0], conn[1], 0.1, conn[3]))
        return new_list
    else:
        return from_list

def test_pop(pop, test_data, exec_thing, spike_fitness):#, noise_rate=50, noise_weight=1):
    #test the whole population and return scores
    global all_fails
    # global empty_pre_count
    global empty_post_count
    global not_needed_ends
    global working_ends
    print "start"
    # gen_stats(pop)
    # save_champion(pop)
    # tracker.print_diff()

    #Acquire all connection matrices and node types

    print(len(pop))
    print(test_data)
    # tracker.print_diff()
    #create the SpiNN nets
    scores = []
    spike_counts = []
    try_except = 0
    while try_except < try_attempts:
        print config
        input_pops = []
        model_count = -1
        bandit_arms = []
        # receive_on_pops = []
        hidden_node_pops = []
        hidden_count = -1
        hidden_marker = []
        output_pops = []
        # Setup pyNN simulation
        try:
            p.setup(timestep=1.0)
            p.set_number_of_neurons_per_core(p.IF_cond_exp, 100)
        except:
            print "set up failed, trying again"
            try:
                p.setup(timestep=1.0)
                p.set_number_of_neurons_per_core(p.IF_cond_exp, 100)
            except:
                print "set up failed, trying again for the last time"
                p.setup(timestep=1.0)
                p.set_number_of_neurons_per_core(p.IF_cond_exp, 100)
        for i in range(len(pop)):
            number_of_nodes = len(pop[i][1].nodes)
            hidden_size = number_of_nodes - output_size

            [i2i_ex, i2h_ex, i2o_ex, h2i_ex, h2h_ex, h2o_ex, o2i_ex, o2h_ex, o2o_ex, i2i_in, i2h_in, i2o_in, h2i_in, h2h_in, h2o_in, o2i_in, o2h_in, o2o_in] = \
                connect_genes_to_fromlist(number_of_nodes, pop[i][1].connections, pop[i][1].nodes)
            # Create environment population

            model_count += 1
            if exec_thing == 'pen':
                # one of these variable can be replaced with test_data depending on what needs to be tested
                input_model = Pendulum(encoding=encoding,
                                       time_increment=time_increment,
                                       pole_length=pole_length,
                                       pole_angle=test_data[0],
                                       reward_based=reward_based,
                                       force_increments=force_increments,
                                       max_firing_rate=max_firing_rate,
                                       number_of_bins=number_of_bins,
                                       central=central,
                                       bin_overlap=bin_overlap,
                                       tau_force=tau_force,
                                       rand_seed=[np.random.randint(0xffff) for j in range(4)],
                                       label='pendulum_pop_{}-{}'.format(model_count, i))
            elif exec_thing == 'rank pen':
                input_model = Rank_Pendulum(encoding=encoding,
                                            time_increment=time_increment,
                                            pole_length=pole_length,
                                            pole_angle=test_data[0],
                                            reward_based=reward_based,
                                            force_increments=force_increments,
                                            max_firing_rate=max_firing_rate,
                                            number_of_bins=number_of_bins,
                                            central=central,
                                            bin_overlap=bin_overlap,
                                            tau_force=tau_force,
                                            rand_seed=[np.random.randint(0xffff) for j in range(4)],
                                            label='rank_pendulum_pop_{}-{}'.format(model_count, i))
            elif exec_thing == 'double pen':
                input_model = DoublePendulum(encoding=encoding,
                                             time_increment=time_increment,
                                             pole_length=pole_length,
                                             pole_angle=test_data[0],
                                             pole2_length=pole2_length,
                                             pole2_angle=0,  # -test_data[0],
                                             reward_based=reward_based,
                                             force_increments=force_increments,
                                             max_firing_rate=max_firing_rate,
                                             number_of_bins=number_of_bins,
                                             central=central,
                                             bin_overlap=bin_overlap,
                                             tau_force=tau_force,
                                             rand_seed=[np.random.randint(0xffff) for j in range(4)],
                                             label='double_pendulum_pop_{}-{}'.format(model_count, i))
            elif exec_thing == 'bout':
                input_model = Breakout(x_factor=x_factor,
                                       y_factor=y_factor,
                                       bricking=bricking,
                                       random_seed=[np.random.randint(0xffff) for j in range(4)],
                                       label='breakout_pop_{}-{}'.format(model_count, i))
            elif exec_thing == 'logic':
                input_model = gym.Logic(truth_table=truth_table,
                                        input_sequence=test_data,
                                        stochastic=stochastic,
                                        rand_seed=[np.random.randint(0xffff) for j in range(4)],
                                        label='logic_pop_{}-{}'.format(model_count, i))
            elif exec_thing == 'arms':
                input_model = Bandit(arms=test_data,
                                     reward_delay=duration_of_trial,
                                     reward_based=reward_based,
                                     rand_seed=[np.random.randint(0xffff) for j in range(4)],
                                     label='bandit_pop_{}-{}'.format(model_count, i))
            else:
                print "Incorrect input model selected"
                raise Exception
            input_pop_size = input_model.neurons()
            input_pops.append(p.Population(input_pop_size, input_model))
            # added to ensure that the arms and bandit are connected to and from something
            null_pop = p.Population(1, p.IF_cond_exp(), label='null{}'.format(i))
            p.Projection(input_pops[model_count], null_pop, p.AllToAllConnector())
            if fast_membrane:
                output_pops.append(p.Population(output_size, p.IF_cond_exp(tau_m=0.5, # parameters for a fast membrane
                                                                      tau_refrac=0,
                                                                      v_thresh=-64,
                                                                      tau_syn_E=0.5,
                                                                      tau_syn_I=0.5),
                                               label='output_pop_{}-{}'.format(model_count, i)))
            else:
                output_pops.append(p.Population(output_size, p.IF_cond_exp(),
                                               label='output_pop_{}-{}'.format(model_count, i)))
            if spike_fitness == 'out':
                output_pops[model_count].record('spikes')
            p.Projection(output_pops[model_count], input_pops[model_count], p.AllToAllConnector())
            if noise_rate != 0:
                output_noise = p.Population(output_size, p.SpikeSourcePoisson(rate=noise_rate), label="output noise")
                p.Projection(output_noise, output_pops[i], p.OneToOneConnector(),
                             p.StaticSynapse(weight=noise_weight), receptor_type='excitatory')

            if hidden_size != 0:
                hidden_node_pops.append(p.Population(hidden_size, p.IF_cond_exp(), label="hidden_pop {}".format(i)))
                hidden_count += 1
                hidden_marker.append(i)
                if noise_rate != 0:
                    hidden_noise = p.Population(hidden_size, p.SpikeSourcePoisson(rate=noise_rate), label="hidden noise")
                    p.Projection(hidden_noise, hidden_node_pops[hidden_count], p.OneToOneConnector(),
                                 p.StaticSynapse(weight=noise_weight), receptor_type='excitatory')
                if spike_fitness:
                    hidden_node_pops[hidden_count].record('spikes')
            # output_pops[i].record('spikes')

            # Create the remaining nodes from the connection matrix and add them up
            # if len(i2i_ex) != 0:
            #     connection = p.FromListConnector(i2i_ex)
            #     p.Projection(input_pops[model_count], input_pops[model_count], connection,
            #                  receptor_type='excitatory')
            if len(i2h_ex) != 0:
                connection = p.FromListConnector(i2h_ex)
                p.Projection(input_pops[model_count], hidden_node_pops[hidden_count], connection,
                             receptor_type='excitatory')
            if len(i2o_ex) != 0:
                # connect_to_arms(input_pops[model_count], i2o_ex, bandit_arms[i], 'excitatory')
                i2o_ex = parse_connections(i2o_ex)
                connection = p.FromListConnector(i2o_ex)
                p.Projection(input_pops[model_count], output_pops[i], connection,
                             receptor_type='excitatory')
            # if len(h2i_ex) != 0:
            #     p.Projection(hidden_node_pops[hidden_count], input_pops[model_count], p.FromListConnector(h2i_ex),
            #                  receptor_type='excitatory')
            if len(h2h_ex) != 0:
                p.Projection(hidden_node_pops[hidden_count], hidden_node_pops[hidden_count], p.FromListConnector(h2h_ex),
                             receptor_type='excitatory')
            if len(h2o_ex) != 0:
                h2o_ex = parse_connections(h2o_ex)
                # connect_to_arms(hidden_node_pops[hidden_count], h2o_ex, bandit_arms[i], 'excitatory')
                p.Projection(hidden_node_pops[hidden_count], output_pops[i], p.FromListConnector(h2o_ex),
                             receptor_type='excitatory')
            # if len(o2i_ex) != 0:
            #     p.Projection(output_pops[i], input_pops[model_count], p.FromListConnector(o2i_ex),
            #                  receptor_type='excitatory')
            if len(o2h_ex) != 0:
                p.Projection(output_pops[i], hidden_node_pops[hidden_count], p.FromListConnector(o2h_ex),
                             receptor_type='excitatory')
            if len(o2o_ex) != 0:
                o2o_ex = parse_connections(o2o_ex)
                p.Projection(output_pops[i], output_pops[i], p.FromListConnector(o2o_ex),
                             receptor_type='excitatory')
            # if len(i2i_in) != 0:
            #     p.Projection(input_pops[model_count], input_pops[model_count], p.FromListConnector(i2i_in),
            #                  receptor_type='inhibitory')
            if len(i2h_in) != 0:
                p.Projection(input_pops[model_count], hidden_node_pops[hidden_count], p.FromListConnector(i2h_in),
                             receptor_type='inhibitory')
            if len(i2o_in) != 0:
                i2o_in = parse_connections(i2o_in)
                # connect_to_arms(input_pops[model_count], i2o_in, bandit_arms[i], 'inhibitory')
                p.Projection(input_pops[model_count], output_pops[i], p.FromListConnector(i2o_in),
                             receptor_type='inhibitory')
            # if len(h2i_in) != 0:
            #     p.Projection(hidden_node_pops[hidden_count], input_pops[model_count], p.FromListConnector(h2i_in),
            #                  receptor_type='inhibitory')
            if len(h2h_in) != 0:
                p.Projection(hidden_node_pops[hidden_count], hidden_node_pops[hidden_count], p.FromListConnector(h2h_in),
                             receptor_type='inhibitory')
            if len(h2o_in) != 0:
                h2o_in = parse_connections(h2o_in)
                # connect_to_arms(hidden_node_pops[hidden_count], h2o_in, bandit_arms[i], 'inhibitory')
                p.Projection(hidden_node_pops[hidden_count], output_pops[i], p.FromListConnector(h2o_in),
                             receptor_type='inhibitory')
            # if len(o2i_in) != 0:
            #     p.Projection(output_pops[i], input_pops[model_count], p.FromListConnector(o2i_in),
            #                  receptor_type='inhibitory')
            if len(o2h_in) != 0:
                p.Projection(output_pops[i], hidden_node_pops[hidden_count], p.FromListConnector(o2h_in),
                             receptor_type='inhibitory')
            if len(o2o_in) != 0:
                o2o_in = parse_connections(o2o_in)
                p.Projection(output_pops[i], output_pops[i], p.FromListConnector(o2o_in),
                             receptor_type='inhibitory')
            # if len(i2i_in) == 0 and len(i2i_ex) == 0 and \
            if len(i2h_in) == 0 and len(i2h_ex) == 0and \
                    len(i2o_in) == 0 and len(i2o_ex) == 0:
                print "empty out from bandit, adding empty pop to complete link"
                empty_post = p.Population(1, p.IF_cond_exp(), label="empty_post {}".format(i))
                p.Projection(input_pops[model_count], empty_post, p.AllToAllConnector())
                empty_post_count += 1

        print "reached here 1"
        # tracker.print_diff()

        simulator = get_simulator()
        try:
            p.run(runtime)
            try_except = try_attempts
            print "successful run"
            break
        except:
            traceback.print_exc()
            try:
                globals_variables.unset_simulator()
                working_ends += 1
            except:
                traceback.print_exc()
                not_needed_ends += 1
            all_fails += 1
            try_except += 1
            print "\nfailed to run on attempt", try_except, ". total fails:", all_fails, "\n" \
                    "ends good/bad:", working_ends, "/", not_needed_ends
            if try_except >= try_attempts:
                print "calling it a failed population, splitting and rerunning"
                return 'fail'


    hidden_count = 0
    out_spike_count = [0 for i in range(len(pop))]
    hid_spike_count = [0 for i in range(len(pop))]
    if spike_fitness:
        for i in range(len(pop)):
            print "gathering spikes for ", i
            if spike_fitness == 'out':
                spikes = output_pops[i].get_data('spikes').segments[0].spiketrains
                for neuron in spikes:
                    for spike in neuron:
                        out_spike_count[i] += 1
            if i in hidden_marker:
                spikes = hidden_node_pops[hidden_count].get_data('spikes').segments[0].spiketrains
                hidden_count += 1
                for neuron in spikes:
                    for spike in neuron:
                        hid_spike_count[i] += 1
            else:
                print "no hidden ", i

    print "reached here 2"
    scores = []
    for i in range(len(pop)):
        scores.append(get_scores(game_pop=input_pops[i], simulator=simulator))
    p.end()
    pop_fitnesses = []
    for i in range(len(pop)):
        if spike_fitness:
            pop_fitnesses.append([scores[i][len(scores[i])-1][0], hid_spike_count[i] + out_spike_count[i]])
        else:
            pop_fitnesses.append([scores[i][len(scores[i])-1][0]])
        print i, pop_fitnesses[i]

    return pop_fitnesses

def print_fitnesses(fitnesses):
    # with open('fitnesses {} {}.csv'.format(config, test_id), 'w') as file:
    #     writer = csv.writer(file, delimiter=',', lineterminator='\n')
    #     for fitness in fitnesses:
    #         writer.writerow(fitness)
    #     file.close()
    np.save('fitnesses {} {}.npy'.format(config, test_id), fitnesses)

def read_globals(config):
    file_name = 'globals {}.csv'.format(config)
    with open(file_name) as from_file:
        csvFile = csv.reader(from_file)
        for row in csvFile:
            try:
                globals()[row[0]] = literal_eval(row[1])
            except:
                print "",
                # try:
                #     globals()[row[0]] = row[1]
                # except:
                #     print ""
                # traceback.print_exc()
                # break

print "thing"
# parser = argparse.ArgumentParser(
#     description='just trying to pass a single number into here',
# formatter_class=argparse.RawTextHelpFormatter)
# args = parser.parse_args()
config = sys.argv[1] #literal_eval(args.config)
test_id = sys.argv[2]#literal_eval(args.test_id)
file_name = 'data {} {}.npy'.format(config, test_id)
connections_and_config = np.load(file_name)

read_globals(config)

# fitnesses = pop_test(connections, test_data_set, split, runtime, exposure_time, noise_rate, noise_weight,
#                                reward, size_f, spike_f, True)
fitnesses = test_pop(*connections_and_config)

print_fitnesses(fitnesses)