from core.data import *
import json

try:
  from slugify import slugify
except:
  print("\nInstall python-slugify to migrate:\n> pip install python-slugify")
  exit(1)

with Session(engine) as session:
  with open("operators.json", encoding="utf8") as f:
    operators = json.load(f)
    
    for operator in operators:
      operator_db_users = []

      for user in operator["users"]:
        db_user = session.exec(select(User).where(User.id == user)).one_or_none()

        if db_user == None:
          db_user = User(id=user)
          session.add(db_user)
          print(f"Migrated user <@{user}>")

        operator_db_users.append(db_user)

      db_operator = Operator(
        id=operator["uid"],
        name=operator["name"],
        short=operator["short"],
        color=int(operator["color"][1:], 16),
        users=operator_db_users
      )
      session.add(db_operator)
      print(f"Migrated operator {operator['name']}")

  with open("lines.json", encoding="utf8") as f:
    lines = json.load(f)

    for line in lines:
      line_db_stations = []

      for station in line["stations"]:
        db_station = session.exec(select(Station).where(Station.name == station)).one_or_none()

        if db_station == None:
          db_station = Station(id=slugify(station), name=station)
          session.add(db_station)
          print(f"Migrated station {station}")

        line_db_stations.append(db_station)

      db_line = Line(
        name=line["name"],
        status=LineStatus.from_legacy(line["status"]),
        color=int(line["color"][1:], 16),
        operator_id=line["operator_uid"]
      )
      session.add(db_line)

      order = 0
      for db_station in line_db_stations:
        link = LineStationLink(line=db_line, station=db_station, order=order)
        session.add(link)
        db_line.stations.append(link)
        order += 1

      print(f"Migrated line {line['name']}")

  session.commit()
