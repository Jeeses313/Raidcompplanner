from mip import Model, xsum, BINARY, OptimizationStatus
import numpy as np
# classes/jobs and their roles in game from jobs.txt in format ['job/class1', 'job/class2', ...] and ['role', 'role', ...]
jobs = [] 
roles = []
with open('jobs.txt', 'r') as file:
    for line in file:
        if line[0] != '#':
            parts = list(line.strip().split(' '))
            jobs.append(parts[0])
            roles.append(parts[1])
roles = np.array(roles)
# names of raiders and class/job wishes of raiders from jobwish.txt
jobwishes = []
names = []
jobwishtable = []
with open('jobwish.txt', 'r') as file:
    for line in file:
        if line[0] != '#':
            parts = list(line.strip().split(' '))
            names.append(parts[0])
            jobwish = [parts[l] for l in range(1, len(parts))]
            jobwishes.append(jobwish)
            jobwishrow = np.array([int(job in jobwish) for job in jobs])
            jobwishtable.append(jobwishrow)
print("Class/Job wishes: ")
for i in range(len(jobwishes)):
    print(names[i] + ": " + ', '.join(jobwishes[i]))
# default raiders needed for raid from number of names
raidersneeded = len(names)
# default duplicate classes/jobs allowed
duplicatesallowed = True
# read the rules from rules.txt
rules = []
with open('rules.txt', 'r') as file:
    for line in file:
        if line[0] != '#':
            parts = list(line.strip().split(' '))
            if parts[0] == 'a':
                raidersneeded = int(parts[2])
            elif parts[0] == 'nd':
                duplicatesallowed = False
            elif len(parts) >= 3:
                rules.append(parts)
# make model
model = Model("plan")
model.verbose = 0
# variables for raiders and their class/job where x[i][j] == 1 iff raider i is of class/job j
raiders = [[model.add_var(var_type=BINARY) for j in range(len(jobs))] for i in range(len(names))]
# add how many raiders are needed
model += xsum(raiders[i][j] for i in range(len(names)) for j in range(len(jobs))) == raidersneeded
# add what classes/jobs raiders want to be and don't want to be
for i in range(len(names)):
    model += xsum(raiders[i][j] for j in np.where(jobwishtable[i] == 1)[0]) <= 1
    model += xsum(raiders[i][j] for j in np.where(jobwishtable[i] == 0)[0]) == 0
# no two raiders can have same class/job if duplicates are not allowed
if not duplicatesallowed:
    for j in range(len(jobs)):
        model += xsum(raiders[i][j] for i in range(len(names))) <= 1
# add limitations to how many of each classes/jobs there can be of each role as given by rules.txt
for rule in rules:
    rolesinrule = np.array([rule[l] for l in range(0, len(rule) - 2)])
    if rule[len(rule) - 2] == '<':
        model += xsum(raiders[i][j] for j in np.concatenate([np.where(roles == rolesinrule[l])[0] for l in range(len(rolesinrule))]) for i in range(len(names))) < int(rule[len(rule) - 1])
    elif rule[len(rule) - 2] == '<=':
        model += xsum(raiders[i][j] for j in np.concatenate([np.where(roles == rolesinrule[l])[0] for l in range(len(rolesinrule))]) for i in range(len(names))) <= int(rule[len(rule) - 1])
    elif rule[len(rule) - 2] == '=':
        model += xsum(raiders[i][j] for j in np.concatenate([np.where(roles == rolesinrule[l])[0] for l in range(len(rolesinrule))]) for i in range(len(names))) == int(rule[len(rule) - 1])
    elif rule[len(rule) - 2] == '>=':
        model += xsum(raiders[i][j] for j in np.concatenate([np.where(roles == rolesinrule[l])[0] for l in range(len(rolesinrule))]) for i in range(len(names))) >= int(rule[len(rule) - 1])
    elif rule[len(rule) - 2] == '>':
        model += xsum(raiders[i][j] for j in np.concatenate([np.where(roles == rolesinrule[l])[0] for l in range(len(rolesinrule))]) for i in range(len(names))) > int(rule[len(rule) - 1])
feasiblecomps = 0
while True:
    print('-------------------------------------------------------')
    print("Solving...")
    status = model.optimize()
    if status == OptimizationStatus.OPTIMAL:
        feasiblecomps += 1
        print("Feasible comp:")
        currentSolution = []
        for i in range(len(names)):
            hasJob = False
            for j in range(len(jobs)):
                if raiders[i][j].x == 1:
                    print(names[i] + ": " + jobs[j])
                    currentSolution.append(np.array([i, j]))
                    hasJob = True
                    break
            if not hasJob:
                print(names[i] + ": not raiding")
        answer = input("Find another solution (y/n): ")
        if answer != 'y':
            break
        # add current solution as constraint to find another solution
        model += xsum(raiders[solution[0]][solution[1]] for solution in currentSolution) <= raidersneeded - 1
    else: 
        if feasiblecomps > 0:
            print("No other feasible comps left.")
        else:
            print("No feasible comps. Since no feasible comps were found: 1. check if everything is correct in the text files, 2. ask one of the raiders to chnage their wishes or 3. get a new raider.")
        break
