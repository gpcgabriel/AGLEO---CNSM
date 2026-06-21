from ..process_unit import ProcessUnit
from ..satellite import Satellite
from ..user import User
from geopy.distance import geodesic
from math import sqrt
import networkx as nx


def has_path(topology, origin, target):
    for access_point in origin.network_access_points:
        if nx.has_path(G=topology, source=access_point, target=target):
            return True
    return False


def distance(coordinates1, coordinates2):
    if coordinates1 is None or coordinates2 is None:
        return float('inf')
    ground_distance = geodesic(coordinates1[:2], coordinates2[:2]).kilometers
    air_distance = (coordinates1[2] - coordinates2[2]) / 1000
    return sqrt(ground_distance**2 + air_distance**2)


def latency_aware_allocation(model, parameters):
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

        user_coords = access_model.user.coordinates
        target = min(
            process_units,
            key=lambda pu: distance(user_coords, pu.coordinates) if pu.coordinates else float('inf')
        )

        if target != access_model.application.process_unit:
            access_model.application.provision(target)
