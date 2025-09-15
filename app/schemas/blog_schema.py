from enum import Enum


class BlogStatusEnum(str, Enum):
    PENDING = "PENDING"
    CANCELED = "CANCELED"
    PAID = "PAID"
 
class UserRoleEnum(str, Enum):
    ADMIN = "ADMIN"
    USER = "USER"
    GUEST = "GUEST"
    REPORTER = "REPORTER"
 
class UserStatusEnum(str, Enum):
    ACTIVE = "ACTIVE" #DEFAULT
    INACTIVE = "INACTIVE"      
    BLOCK = "BLOCK"            
    BANNED = "BANNED"          
    DELETED = "DELETED"        
    PENDING = "PENDING"        
    SUSPENDED = "SUSPENDED"    
 
class BlogStatusEnum(str, Enum):
    PENDING = "PENDING"
    CANCELED = "CANCELED"
    PAID = "PAID"

