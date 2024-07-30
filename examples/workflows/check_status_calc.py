import sys
from aiida.orm import load_group, load_node

if len(sys.argv) != 2:
    raise Exception("Must give 1 argument with the node number")



group = load_group(pk=int(sys.argv[1]))
for calc_node in group.nodes:

    if calc_node.is_finished:
        print(f'Node<{calc_node.pk}> finished with exit status {calc_node.exit_code}') 
    else: 
        print(f'Node<{calc_node.pk}> still in queue') 

    if calc_node.is_finished_ok:
        print(f'Node<{calc_node.pk}> finished successfully with exit status {calc_node.exit_code}')

    if calc_node.is_failed:
        print(f'Node<{calc_node.pk}> failed  with exit status {calc_node.exit_code}')
     