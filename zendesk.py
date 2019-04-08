from datetime import datetime, timedelta
import sys
import csv
from dateutil import parser

 # common, assumed knowledge
TIME_TAKEN_TO_NEXT_STATION = 2
TIME_TAKEN_TO_CHANGE_LINE = 5
MAX_INT = sys.maxsize

class Network:
  def __init__(self, nodes):
    self.nodes = nodes

  def construct_graph(self, node_list, date): # to determine hour-related info wrt distances
    graph = [[0 for origin in node_list] for dest in node_list]
    for origin_idx in range(len(node_list)):
      for dest_idx in range(len(node_list)):
        try:
          if origin_idx == dest_idx-1 or origin_idx == dest_idx+1:
            if node_list[origin_idx].line == node_list[origin_idx+1].line:
              line = node_list[origin_idx].line
              graph[origin_idx][dest_idx] = get_time_taken_to_next_station(line, date)
        except:
          pass
        if node_list[origin_idx].name == node_list[dest_idx].name:
          if node_list[origin_idx].line != node_list[dest_idx].line:
            graph[origin_idx][dest_idx] = get_time_taken_to_change_line(date)
    return graph

  # return node with min distance and is not visited yet
  # i.e. in queue and therefore should be the next to be visited
  def min_distance(self, dist, queue):
    min_dist = MAX_INT
    min_index = -1

    for i in range(len(dist)):
      if dist[i] < min_dist and i in queue:
        min_dist = dist[i]
        min_index = i
    return min_index

  def get_applicable_nodes(self, date): # to determine hour-related info wrt station availability
    applicable_nodes = []
    for node in self.nodes:
      # allow stations that were built before traveling time
      if node.date <= date:
        applicable_nodes.append(node) # no BONUS part
    return applicable_nodes

  # return first station whose name matches
  def get_node_idx(self, name, applicable_nodes):
    for node_idx in range(len(applicable_nodes)):
      if applicable_nodes[node_idx].name == name:
        return node_idx
    return None

  # for when the start and end nodes are actually the same station, just different codes (interchange)
  def simplify_path(self, applicable_nodes, path):
    if len(path) > 1:
      if applicable_nodes[path[0]].name == applicable_nodes[path[1]].name:
        path = path[1:]
      if applicable_nodes[path[-1]].name == applicable_nodes[path[-2]].name:
        path = path[:-1]
    return path

  def dijkstra(self, origin, dest, graph):
    num_of_nodes = len(graph)
    dist = [MAX_INT for node in graph]
    dist[origin] = 0
    parent = [None for node in graph]

    queue = []
    for i in range(num_of_nodes):
      queue.append(i)

    while queue:
      visited_node = self.min_distance(dist, queue)
      queue.remove(visited_node)
      for i in range(num_of_nodes):
        # consider unvisited other nodes, and where there exists an edge i.e. unvisited neighbors
        if graph[visited_node][i] and i in queue:
          if dist[visited_node] + graph[visited_node][i] < dist[i]:
            dist[i] = dist[visited_node] + graph[visited_node][i]
            parent[i] = visited_node
    path = []
    parent_node = dest
    while parent_node != None:
      path = [parent_node] + path
      parent_node = parent[parent_node]
    return path

  def get_instructions(self, applicable_nodes, path):
    instruction_list = []
    current_line = applicable_nodes[path[0]].line
    last_station = applicable_nodes[path[0]].name
    for step in path:
      next_line = applicable_nodes[step].line
      if next_line != current_line:
        instruction = 'Take '+current_line+' from '+last_station+' to '+applicable_nodes[step].name
        instruction_list.append(instruction)
        instruction = 'Change to line '+next_line
        instruction_list.append(instruction)
        current_line = next_line
        last_station = applicable_nodes[step].name
    instruction = 'Take '+current_line+' from '+last_station+' to '+applicable_nodes[path[-1]].name
    instruction_list.append(instruction)
    return instruction_list

  def get_route(self, origin, dest, date):
    applicable_nodes = self.get_applicable_nodes(date)
    graph = self.construct_graph(applicable_nodes, date)
    origin_idx = self.get_node_idx(origin, applicable_nodes)
    dest_idx = self.get_node_idx(dest, applicable_nodes)
    if origin_idx == None:
      print('The origin station is not opened yet at this point in time.')
      return None
    elif dest_idx == None:
      print('The destination station is not opened yet at this point in time.')
      return None
    path = self.dijkstra(origin_idx, dest_idx, graph)
    path = self.simplify_path(applicable_nodes, path)
    instructions = self.get_instructions(applicable_nodes, path)
    return instructions

# an interchange comprising of n lines is considered n different nodes
class Node:
  def __init__(self, code, name, date):
    self.code = code # station code is unique but not name bc interchange
    self.name = name
    self.date = date
    self.line = code[:2]

  def __str__(self):
    return self.code + ' (' + self.name + ')'

def process_info(filename):
  with open(filename) as csv_file:
    csv_reader = csv.reader(csv_file, delimiter=',')
    line_count = 0
    all_nodes = []
    all_ids = []
    by_ids = {}
    for row in csv_reader:
      if line_count > 0:
        code = row[0]
        name = row[1]
        date = parser.parse(row[2])
        node = Node(code, name, date)
        all_ids.append(code)
        by_ids[code] = node
        all_nodes.append(node)
      line_count += 1
    return {'all_ids': all_ids, 'by_ids': by_ids, 'all_nodes': all_nodes}

# HELPER FUNCTIONS:
def is_within_peak_hours(date): # 6AM to 9AM and 6PM to 9PM on Mon-Fri
  morning_start = date.replace(hour=6, minute=0)
  morning_end = date.replace(hour=9, minute=0)
  evening_start = date.replace(hour=18, minute=0)
  evening_end = date.replace(hour=21, minute=0)
  if date.weekday() < 5: # is from Mon to Fri
    if (date >= morning_start and date < morning_end) or (date >= evening_start and date <= evening_end):
      return True
  return False

def is_within_non_peak_hours(date): # 9AM to 6PM on Mon-Fri, 6AM to 10PM on Sat-Sun
  weekday_start = date.replace(hour=9, minute=0)
  weekday_end = date.replace(hour=18, minute=0)
  weekend_start = date.replace(hour=6, minute=0)
  weekend_end = date.replace(hour=22, minute=0)
  if date.weekday() < 5: # is from Mon to Fri
    if date >= weekday_start and date < weekday_end:
      return True
  else:
    if date >= weekend_start and date < weekend_end:
      return True
  return False

def is_within_night_hours(date): # 10PM to 6AM
  start = date.replace(hour=22, minute=0)
  end = date.replace(hour=9, minute=0) + timedelta(days=1)
  return date >= start and date < end

def print_instructions(li):
  for item in li:
      print(item)

def levenshtein(s1, s2):
  if len(s1) < len(s2):
    return levenshtein(s2, s1)

  # len(s1) >= len(s2)
  if len(s2) == 0:
    return len(s1)

  previous_row = range(len(s2) + 1)
  for i, c1 in enumerate(s1):
    current_row = [i + 1]
    for j, c2 in enumerate(s2):
      insertions = previous_row[j + 1] + 1 # j+1 instead of j since previous_row and current_row are one character longer
      deletions = current_row[j] + 1       # than s2
      substitutions = previous_row[j] + (c1 != c2)
      current_row.append(min(insertions, deletions, substitutions))
    previous_row = current_row

  return previous_row[-1]

def get_time_taken_to_next_station(line, date):
  if is_within_peak_hours(date):
    if line in ['NS', 'NE']:
      return 12
    else:
      return 10
  elif is_within_non_peak_hours(date):
    if line in ['DT', 'TE']:
      return 8
    else:
      return 10
  elif is_within_night_hours(date):
    if line == 'TE':
      return 8
    else:
      return 10
  else:
    return TIME_TAKEN_TO_NEXT_STATION

def get_time_taken_to_change_line(date):
  if is_within_peak_hours(date):
    return 15
  elif is_within_non_peak_hours(date) or is_within_night_hours(date):
    return 10
  else:
    return TIME_TAKEN_TO_CHANGE_LINE

def bonus_process_applicable_nodes(node_list, date):
  applicable_nodes = []
  for node in node_list:
    if not (is_within_night_hours(date) and node.line in ['DT', 'CG', 'CE']):
      applicable_nodes.append(node)
  return applicable_nodes

def find_station_by_name(keywords, all_stations):
  minimum = MAX_INT
  current_station = None
  for station in all_stations:
    dist = levenshtein(keywords, station.name.upper())
    if dist < minimum:
      minimum = dist
      current_station = station
  return current_station

def find_station_by_code(keywords, all_ids, by_ids):
  if keywords in all_ids:
    return by_ids[keywords]
  return None

def find_station(keywords, all_ids, by_ids, all_stations):
  search_words = keywords.upper().strip()
  res = find_station_by_code(search_words, all_ids, by_ids)
  if res == None:
    return find_station_by_name(search_words, all_stations)
  else:
    return res

def get_input_station(all_ids, by_ids, all_nodes, position):
  keywords = input('Enter the '+position+' station\'s name or code: ')
  station = find_station(keywords, all_ids, by_ids, all_nodes)
  confirmation = input('Is '+station.name+' the correct station?\nType \'y\' to confirm, any other key to search again: ')
  while confirmation.lower() != 'y':
    keywords = input('Enter a station\'s name or code: ')
    station = find_station(keywords, all_ids, by_ids, all_nodes)
    confirmation = input('Is '+station.name+' the correct station?\nType \'y\' to confirm, any other key to search again: ')
  return station

def main():
  res = process_info('StationMap.csv')
  all_nodes = res['all_nodes']
  all_ids = res['all_ids']
  by_ids = res['by_ids']
  network = Network(all_nodes)
  print('Welcome to Minh\'s MRT Route Finding System.')
  command = ''
  while command != 'n':
    origin = get_input_station(all_ids, by_ids, all_nodes, 'origin')
    end = get_input_station(all_ids, by_ids, all_nodes, 'destination')
    input_start_time = input('When do you want to start your journey?\nType \'now\' to start now, any other key to customize time: ')
    if input_start_time.lower().strip() == 'now':
      start_time = datetime.now()
    else:
      invalid = True
      while invalid:
        input_time = input('Type the time in HH:mm 24-hour format (e.g. 21:09)\n')
        input_date = input('Type the date in DD/MM/YYY format (e.g. 20/08/1995)\n')
        try:
          start_time = parser.parse(input_time+', '+input_date)
          invalid = False
        except:
          print('Format is invalid. Please type again.')
    print('Calculating route from '+origin.name+' to '+end.name+' at '+start_time.strftime('%H:%M, %d/%m/%Y'))
    print('Please wait...')
    route = network.get_route(origin.name, end.name, start_time)
    try:
      print_instructions(route)
      command = input('Route has been found. Continue finding another route?\nType \'n\' to stop programme, any other key to continue: ')
    except:
      command = input('An error has occured. Continue finding another route?\nType \'n\' to stop programme, any other key to continue: ')

if __name__ == '__main__':
  main()
