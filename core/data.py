from sqlmodel import *
from enum import Enum

def lmap(*args):
  return list(map(*args))

# -- SCHEMA --
# linkers
class LineStationLink(SQLModel, table=True):
  line_id: str | None = Field(default=None, foreign_key="line.id", primary_key=True)
  station_id: int | None = Field(default=None, foreign_key="station.id", primary_key=True)

class UserOperatorLink(SQLModel, table=True):
  user_id: str | None = Field(default=None, foreign_key="user.id", primary_key=True)
  operator_id: str | None = Field(default=None, foreign_key="operator.id", primary_key=True)

# users
class User(SQLModel, table=True):
  id: str = Field(primary_key=True)
  operators: list["Operator"] = Relationship(back_populates="users", link_model=UserOperatorLink)

# operators
class Operator(SQLModel, table=True):
  id: str = Field(primary_key=True)
  name: str
  short: str
  color: int

  lines: list["Line"] = Relationship(back_populates="operator")
  users: list[User] = Relationship(back_populates="operators", link_model=UserOperatorLink)

  def get_legacy():
    with Session(engine) as session:
      operators = session.exec(select(Operator))
      return lmap(
        lambda operator:
          {
            "name": operator.name,
            "short": operator.short, 
            "color": "#%06x" % (operator.color & 0xffffff),
            "users": lmap(lambda user: user.id, operator.users),
            "uid": operator.id
          },
        operators
      )

# stations
class Station(SQLModel, table=True):
  id: str = Field(primary_key=True)
  name: str

  lines: list["Line"] = Relationship(back_populates="stations", link_model=LineStationLink)

# lines
class LineStatus(Enum):
  RUNNING = 0
  DELAYS = 1
  SUSPENDED = 2
  NO_SERVICE = 3

  def get_legacy(self):
    match self:
      case LineStatus.RUNNING:
        return "Running"
      case LineStatus.DELAYS:
        return "Possible delays"
      case LineStatus.SUSPENDED:
        return "Suspended"
      case LineStatus.NO_SERVICE:
        return "No scheduled service"
      
  def from_legacy(string: str):
    match string:
      case "Running":
        return LineStatus.RUNNING
      case "Possible delays":
        return LineStatus.DELAYS
      case "Suspended":
        return LineStatus.SUSPENDED
      case "No scheduled service":
        return LineStatus.NO_SERVICE

class Line(SQLModel, table=True):
  id: int | None = Field(default=None, primary_key=True)
  name: str
  status: LineStatus = Field(default=LineStatus.RUNNING)
  notice: str | None = Field(default=None)
  color: int

  stations: list[Station] = Relationship(back_populates="lines", link_model=LineStationLink)

  operator_id: str | None = Field(default=None, foreign_key="operator.id")
  operator: Operator | None = Relationship(back_populates="lines")

  def exists(session: Session, name: str):
    return session.exec(select(Line).where(Line.name == name)).one_or_none() != None
    
  def get_legacy():
    with Session(engine) as session:
      lines = session.exec(select(Line))

      return lmap(
        lambda line:
          {
            "name": line.name,
            "status": line.status.get_legacy(),
            "notice": line.notice if line.notice != None else "",
            "color": "#%06x" % (line.color & 0xffffff),
            "stations": lmap(lambda station: station.name, line.stations),
            "operator": line.operator.name,
            "operator_uid": line.operator.id
          },
        lines
      )

# -- INIT --
file = "db.sqlite"

engine = create_engine(f"sqlite:///{file}", echo=True)
SQLModel.metadata.create_all(engine)
