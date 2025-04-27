from sqlmodel import *
from enum import Enum
from typing import Callable, Iterable, TypeVar

_LMapInput = TypeVar("LMapInput")
_LMapOutput = TypeVar("LMapOutput")
def lmap(func: Callable[[_LMapInput], _LMapOutput], iterable: Iterable[_LMapInput]) -> list[_LMapOutput]:
  return list(map(func, iterable))

# -- SCHEMA --
# linkers
class LineStationLink(SQLModel, table=True):
  line_id: str | None = Field(default=None, foreign_key="line.id", primary_key=True)
  line: "Line" = Relationship(back_populates="stations")

  station_id: int | None = Field(default=None, foreign_key="station.id", primary_key=True)
  station: "Station" = Relationship(back_populates="lines")

  order: int

class UserOperatorLink(SQLModel, table=True):
  user_id: str | None = Field(default=None, foreign_key="user.id", primary_key=True)
  operator_id: str | None = Field(default=None, foreign_key="operator.id", primary_key=True)

# users
class User(SQLModel, table=True):
  id: str = Field(primary_key=True)
  operators: list["Operator"] = Relationship(back_populates="users", link_model=UserOperatorLink)

  display_name: str | None
  username: str | None
  avatar_hash: str | None

  def get_default_avatar_url():
    return "https://cdn.discordapp.com/embed/avatars/0.png"

  def get_avatar_url(self):
    if self.avatar_hash == None:
      return User.get_default_avatar_url()
    
    return f"https://cdn.discordapp.com/avatars/{self.id}/{self.avatar_hash}.png"

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

  lines: list[LineStationLink] = Relationship(back_populates="station")

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

  stations: list[LineStationLink] = Relationship(back_populates="line")

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
            "stations": lmap(lambda l: l.station.name, line.get_ordered_stations()),
            "operator": line.operator.name,
            "operator_uid": line.operator.id
          },
        lines
      )
    
  def get_ordered_stations(self):
    return sorted(self.stations, key=lambda l: l.order)

# -- INIT --
file = "db.sqlite"

engine = create_engine(f"sqlite:///{file}")
SQLModel.metadata.create_all(engine)
