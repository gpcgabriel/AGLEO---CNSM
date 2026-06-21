from ..process_unit import ProcessUnit
from ..satellite import Satellite
from ..user import User
import networkx as nx


def has_path(topology, origin, target):
    for access_point in origin.network_access_points:
        if nx.has_path(G=topology, source=access_point, target=target):
            return True
    return False


def load_ratio(unit):
    cpu_ratio = unit.cpu_demand / unit.cpu if unit.cpu > 0 else 1.0
    mem_ratio = unit.memory_demand / unit.memory if unit.memory > 0 else 1.0
    sto_ratio = unit.storage_demand / unit.storage if unit.storage > 0 else 1.0
    return cpu_ratio + mem_ratio + sto_ratio


def load_balanced_allocation(model, parameters):
    applications_to_be_allocated = []

    for user in User.all():
        for access_model in user.applications_access_models:
            if not access_model.request_provisioning and access_model.application.available:
                access_model.application.deprovision()
            elif access_model.request_provisioning and not access_model.application.available:
                applications_to_be_allocated.append(access_model)
            else:
                process_unit = access_model.application.process_unit
                if not any(
                    (process_unit in model.topology.neighbors(ap) for ap in user.network_access_points)
                ) or user.network_access_points == []:
                    applications_to_be_allocated.append(access_model)

    for access_model in applications_to_be_allocated:
        process_units = []

        for access_point in access_model.user.network_access_points:
            if isinstance(access_point, Satellite) and getattr(access_point, 'process_unit') is not None:
                pu = access_point.process_unit
                if pu.has_capacity_to_host(access_model.application) and pu.available:
                    process_units.append(pu)

        if not process_units:
            if parameters['ground_station'].process_unit:
                for unit in parameters['ground_station'].process_unit:
                    if unit.has_capacity_to_host(access_model.application) and unit.available and has_path(model.topology, access_model.user, unit):
                        process_units.append(unit)

        if not process_units:
            if access_model.application.available:
                access_model.application.deprovision()
            continue

        target = min(process_units, key=load_ratio)

        if target != access_model.application.process_unit:
            access_model.application.provision(target)
