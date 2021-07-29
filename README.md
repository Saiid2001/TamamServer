# TamamServer

## Relationships API
base url: `/relations`

---
### Endpoints
#### `/relations/`
> Gets all relations for the requesting user. 

**parameters:** None

**return:** List of all relation Links.
```
[
    {
        "_id": string - id of relation, 
        "status": string ['requested', 'established'], 
        "type": string ['friendship',...], 
        "user1": string - id of user, 
        "user2": string - id of user
    },
    ...
]
``` 

####  `/relations/<user_id>`
> Gets all relations between the requesting user and the user in the path

**parameters:** user_id (part of path)

**return:** Dictionary with keys type of relations `friendship`, `request-sent`, `request-received` and values the respective links
```
{
    "friendship": {... link ...}, 
    "request-sent": {... link ...}, 
    "request-received": {... link ...}, 
}
``` 


####  `/relations/friendships`
> Gets all friendships for the requesting user. 

**parameters:** None

**return:** List of friend user Objects with extra attribute `relationship` containing the link data.
```
[
    {
        'firstName': ...,
        ...
        'relationship':{... link ...}
    },
    ...
]
``` 

####  `/relations/friendships/requests/sent`
> Gets all friend requests sent by the requesting user. 

**parameters:** None

**return:** List of user Objects with extra attribute `relationship` containing the link data that user has requested friendship with.
```
[
    {
        'firstName': ...,
        ...
        'relationship':{... link ...}
    },
    ...
]
``` 

####  `/relations/friendships/requests/received`
> Gets all friend requests received by the requesting user. 

**parameters:** None

**return:** List of user Objects with extra attribute `relationship` containing the link data that user has requested friendship with.
```
[
    {
        'firstName': ...,
        ...
        'relationship':{... link ...}
    },
    ...
]
``` 

####  `/relations/friendships/request/<user_id>`
> Sends a friend request from the requesting user to user with `"_id": user_id`

**parameters:** user_id

**return:** Response code 200

####  `/relations/friendships/accept/<user_id>`
> Accepts a friend request sent from user with `"_id": user_id`

**parameters:** user_id

**return:** Response code 200

---
### Socket Events

#### `new-friend-request`
> sent to a user to notify them that they received a friend request

**Data**
```
{'user': Id of user who sent request}
```

#### `friend-request-accepted`
> sent to a user to notify them that their friend request was accepted

**Data**
```
{'user': Id of user who accepted my request}
```





