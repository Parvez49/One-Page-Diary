### enum 
   module provides a way to define named constant values.
### Why Use Enum? 
    ✅ Improves code readability (meaningful names instead of magic numbers).
    ✅ Prevents invalid values (restricted choices).
    ✅ Enhances maintainability (centralized values).

    from enum import Enum, IntEnum, StrEnum, unique
    
    class Status(Enum):
        PENDING = "pending"
        APPROVED = "approved"
        REJECTED = "rejected"

    print(Status.PENDING.value) # pending

    @unique           # enforce unique enum value
    class Status(IntEnum):
      PENDING = 1
      APPROVED = 2
      REJECTED = 3
    
