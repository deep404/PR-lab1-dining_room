# PR-lab1-dining_room

# PR-lab1-kitchen

> Network Programming Laboratory Work No1 [Dining_Room]
>
> FAF 192
>
> Moglan Mihai
> 

More detailed README will be added later!

#### Run

```bash
$ docker build -t dining . # create kitchen image
$ # the docker network (pr_lab1) was created when running kitchen image
$ # now just run the dining image on the same network as kitchen 
$ docker run -d --net pr_lab1 --name dining dining # run docker container on created network
```

