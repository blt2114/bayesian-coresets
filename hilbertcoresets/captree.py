import numpy as np
import heapq

def cap_tree_search(root, yw, y_yw):
  #each UB/LB computation is 2 O(d) operations
  pq = []
  L = -2.
  nopt = -1
  heapq.heappush(pq, (-root.upper_bound(y_yw, yw), root))
  nfun = 2.
  while pq:
    negub, cap = heapq.heappop(pq)
    if -negub > L:
      ell = cap.lower_bound(y_yw, yw)
      nfun += 2.
      if ell > L:
        L = ell
        nopt = cap.ny
      if cap.cR:
        heapq.heappush(pq, (-cap.cR.upper_bound(y_yw, yw), cap.cR))
        heapq.heappush(pq, (-cap.cL.upper_bound(y_yw, yw), cap.cL))
        nfun += 4.
  return nopt, nfun

class CapTree(object):
  def __init__(self, data, idcs=None):
    if idcs is None:
      idcs = np.arange(data.shape[0])
    if idcs.shape[0] == 1:
      self.y = data[idcs[0], :]
      self.xi = data[idcs[0], :]
      self.r = 1.
      self.ny = idcs[0]
      self.cR = None
      self.cL = None
      self.nfun_construction = 2.
    else:
      #compute manifold mean
      self.xi = data[idcs].sum(axis=0)
      xinrm = np.sqrt((self.xi**2).sum())
      if xinrm == 0.:
        self.xi = data[0, :]
      else:
        self.xi /= xinrm
      #get dists to all points
      dots = data[idcs].dot(self.xi)
      #get the closest point to the mean (for LB)
      nY = dots.argmax()
      self.y = data[idcs[nY], :]
      self.ny = idcs[nY]
      #get the furthest point (for r + children)
      nL = dots.argmin()
      self.r = max(-1., min(1., dots[nL])) #to take care of numerical > 1 or < -1
      #get the dists to the L anchor + furthest point
      dotsL = data[idcs].dot(data[idcs[nL], :])
      nR = dotsL.argmin()
      dotsR = data[idcs].dot(data[idcs[nR], :])
      #split based on L/R anchors
      idcsR = dotsR > dotsL
      #if all data are colinear, idcsR/idcsL can be empty, so just split in half
      if np.all(idcsR) or np.all(np.logical_not(idcsR)):
        idcsR = np.arange(idcs.shape[0]) < idcs.shape[0]/2
      self.cR = CapTree(data, idcs[idcsR])
      self.cL = CapTree(data, idcs[np.logical_not(idcsR)])
     
      #a better implementation of the above in c++ would do this many O(d) operations:
      # if leaf
      #  2 operations to store xi and y
      # else
      #   N+2 for summing up data to get xi, normalizing, storing
      #   N+1 to compute argmin / argmax datapoint to xi + save argmax
      #   N to compute argmin (R child) from L child
      #   N to split based on dots from L and R
      self.nfun_construction = self.cR.nfun_construction + self.cL.nfun_construction + 4.*idcs.shape[0]+3.

  def upper_bound(self, u, v):
    #compute upper bound
    bu = self.xi.dot(u)
    bv = self.xi.dot(v)
    b = np.sqrt(max(0., 1.-bu**2-bv**2))
    U = -1.
    rv = np.sqrt(max(0., self.r**2 - bv**2))
    r1 = np.sqrt(max(0., 1.-self.r**2))
    if np.fabs(bv) > self.r or bu >= rv:
      U = 1.
    else:
      U = (bu*rv + b*r1)/(b**2+bu**2)
    return U

  def lower_bound(self, u, v):
    bu = self.y.dot(u)
    bv = self.y.dot(v)
    return bu/np.sqrt(1.-bv**2)

  
