# Maya GetClosestIntersection

This repository is intended to serve as a base introduction into creating a Maya plug-in to cast a ray out into the scene and return the closest intersection. This could be used to extend to a rigging tool for automatically placing locators at the mouse-click location or a tool to interactively drag objects around the scene from a 2d viewpoint.

It comes with several helper functions which can be taken over into larger projects to more easily interface with the Maya API

# Installation

tbd

# Usage

tbd

# Performance

Despite what one might think, the main performance bottlenecks for finding the closest intersection is the Maya API call to `MFnMesh.getClosestIntersection()`. As such, any reduction in the amount of times this function is called will offer considerable reductions in computation time. This may be trivial for small scenes without many objects but can become quite the burden for larger mesh samples as can be seen in the [benchmarks](#benchmarking) below.

To lessen the time required to compute an intersection two different types of spacial acceleration structures have been implemented. Both of these can be found under `/core/acceleration_structures/` and can run entirely independant of each other. The goal of these structures is to be able to quickly "filter" the scene to contain only relevant items.

Keep in mind that the actual call to `MFnMesh.getClosestIntersection()` does also use an acceleration structure in and of itself which can be passed as a parameter to the function. Therefore we are doing the same thing but one level higher.

### Octree

[Octrees](https://en.wikipedia.org/wiki/Octree) are the simpler of the two structures, partitioning the complete scene bounding box into a recursive tree of eights until a certain depth or condition is met. In the case of this implementation, it is bound by depth, as can be seen by its signature.
```py
class Octree:

    def __init__(self, mesh_list: mesh_list.MFnMeshList, bbox: om.MBoundingBox, depth: int = 3):
```

While an octree is simple in construction, in most real-world scenes it will result in an unbalanced tree, i.e. some nodes will be much further down the tree than average. Empty leaf nodes are however culled during the build process to avoid iterating nodes without content. Additionally, this Octree implementation can have a single mesh reside in multiple bounding boxes at the same time. 



### Bounding Volume Hierarchies (BVH)

[Bounding Volume Hierarchies](https://en.wikipedia.org/wiki/Bounding_volume_hierarchy) are a similar type of spacial partitioning, with the major difference being that a mesh can be contained in only a single leaf node for a given tree. Additionally, bounding volumes are fitted around the meshes as much as possible to avoid overlap. This opens up the interesting optimization step, in which intersected bounding boxes can be sorted by distance. This means a closer bounding box is guaranteed to contain a closer mesh. 

Furthermore, the algorithm for splitting the Bounding Boxes is a median split (i.e. half the meshes go in one node, the other half in the other) which creates a much more balanced tree. This can be seen by running `BVH.pprint()` to visualize the binary tree

Finally, in this implementation BVH construction is much faster allowing for much deeper tree levels and therefore less collision tests.

```py
class BVH:

    def __init__(self, mesh_list: mesh_list.MFnMeshList, bbox: om.MBoundingBox, max_depth: int = 20):

```


## Benchmarking

> [!NOTE]
> Please note that these samples were chosen at random in a way that they would still intersect the geometry as a non-intersection leads to a computation time of < 5 ms for the acceleration structures

Specs used for benchmarking
- `Maya 2023.3`
- `CPU: Threadripper 3960x 24-Core` *
- `RAM: 128 GB` 

**Code is only executed on a single of these 24-Cores*


### Car Dataset

---

**Scene Info**
- `Object Count: 5,515`
- `Tri Count: 45,242,012 `


<details open>
    <summary> Results </summary>


|                           | BruteForce    | Octree    | BVH       |
| ---                       | :--------:    | :----:    | :------:  |
| Mesh init                 | 539 ms        | 539 ms    | 539 ms    |
| Max Tree Depth*           | N/A           | 3         | 20        |          
| Accel Structure init      | N/A           | 432 ms    | 75 ms     |
| **Total Initialization**  | **539 ms**    | **971 ms**| **614 ms**|
|                           |               |           |           | 
| *Sample 1*                | *2355 ms*     | *334 ms*  | *139 ms*  |
| *Sample 2*                | *2259 ms*     | *472 ms*  | *107 ms*  |
| *Sample 3*                | *2272 ms*     | *407 ms*  | *68 ms*   |
| *Sample 4*                | *2271 ms*     | *399 ms*  | *176 ms*  |
| *Sample 5*                | *2448 ms*     | *330 ms*  | *90 ms*   |
| *Sample 6*                | *2306 ms*     | *349 ms*  | *47 ms*   |
| *Sample 7*                | *2297 ms*     | *680 ms*  | *85 ms*   |
| *Sample 8*                | *2297 ms*     | *193 ms*  | *39 ms*   |
| *Sample 9*                | *2301 ms*     | *705 ms*  | *74 ms*   |
| *Sample 10*               | *2289 ms*     | *277 ms*  | *23 ms*   |
|                           |               |           |           |
| **Median Average**        | **2297 ms**   | **374 ms**| **80 ms** |
| **Mean Average**          | **2309 ms**   | **415 ms**| **85 ms** |

**Max Tree Depth refers to the maximum allowed depth, not necessarily the maximum actual depth*

</details>

---

### [Disney Moana Island Scene](https://www.disneyanimation.com/resources/moana-island-scene/)

---

**Scene Info**
- `Object Count: 00,000`
- `Tri Count: 00,000,000 `
---
<details open>
    <summary> Full Data </summary>

|                           | BruteForce    | Octree    | BVH       |
| ---                       | :--------:    | :----:    | :------:  |
| Mesh init                 | 000 ms        | 539 ms    | 539 ms    |
| Max Tree Depth*           | N/A           | 3         | 20        |          
| Accel Structure init      | N/A           | 432 ms    | 75 ms     |
| **Total Initialization**  | **539 ms**    | **971 ms**| **614 ms**|
|                           |               |           |           | 
| *Sample 1*                | *0000 ms*     | *000 ms*  | *00 ms*   |
| *Sample 2*                | *0000 ms*     | *000 ms*  | *00 ms*   |
| *Sample 3*                | *0000 ms*     | *000 ms*  | *00 ms*   |
| *Sample 4*                | *0000 ms*     | *000 ms*  | *00 ms*   |
| *Sample 5*                | *0000 ms*     | *000 ms*  | *00 ms*   |
| *Sample 6*                | *0000 ms*     | *000 ms*  | *00 ms*   |
| *Sample 7*                | *0000 ms*     | *000 ms*  | *00 ms*   |
| *Sample 8*                | *0000 ms*     | *000 ms*  | *00 ms*   |
| *Sample 9*                | *0000 ms*     | *000 ms*  | *00 ms*   |
| *Sample 10*               | *0000 ms*     | *000 ms*  | *00 ms*   |
|                           |               |           |           |
| **Median Average**        | **0000 ms**   | **000 ms**| **00 ms** |
| **Mean Average**          | **0000 ms**   | **000 ms**| **00 ms** |

**Max Tree Depth refers to the maximum allowed depth, not necessarily the maximum actual depth*

</details>
