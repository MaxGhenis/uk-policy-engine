"""
Functions to convert URL query parameters into OpenFisca situation initialiser functions.
"""

from openfisca_uk import BASELINE_VARIABLES


def create_situation(params: dict):
    def situation(sim):
        household = {}
        families = {}
        family_members = {}
        people = {}
        for key in params:
            components = key.split("_")
            if components[0] != "policy":
                variable = "_".join(components[:-1])
                entity_id = components[-1]
                try:
                    value = float(params[key])
                except:
                    value = params[key]
                if variable not in BASELINE_VARIABLES and variable != "family":
                    print(f"Skipping variable {variable}")
                if variable == "family" or BASELINE_VARIABLES[variable].entity.key == "person":
                    if entity_id not in people:
                        people[entity_id] = {}
                    if variable == "family":
                        if value not in family_members:
                            family_members[value] = []
                        family_members[value] += [entity_id]
                    else:
                        people[entity_id][variable] = value
                elif BASELINE_VARIABLES[variable].entity.key == "benunit":
                    if entity_id not in families:
                        families[entity_id] = {}
                    families[entity_id][variable] = value
                else:
                    household[variable] = value
        members_of_families = sum(map(list, family_members.values()), [])
        is_adult = lambda p_id: people[p_id]["age"] >= 18
        is_child = lambda p_id: not is_adult(p_id)
        for person in people:
            if "age" not in people[person]:
                people[person]["age"] = 18
            if person not in members_of_families:
                family_names = list(family_members.keys())
                i = 0
                if i == len(family_names):
                    families[str(i + 1)] = {}
                    family_names += [str(i + 1)]
                    family_members[str(i + 1)] = []
                adoptive_family = family_names[i]
                while len(list(filter(is_adult, family_members[adoptive_family]))) >= 2:
                    i += 1
                    if i == len(families):
                        families[str(i + 1)] = {}
                        family_names += [str(i + 1)]
                        family_members[str(i + 1)] = []
                    adoptive_family = family_names[i]
                family_members[adoptive_family] += [person]
        for person_id, person in people.items():
            sim.add_person(**person, name=person_id)
        for family_id, family in families.items():
            sim.add_benunit(**family, adults=list(filter(is_adult, family_members[family_id])), children=list(filter(is_child, family_members[family_id])))
        sim.add_household(**household, adults=list(filter(is_adult, people)), children=list(filter(is_child, people)))
        
        return sim

    return situation
