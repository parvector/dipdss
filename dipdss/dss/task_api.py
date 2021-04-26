from pymoo import *
from dss.models import *
import django
from pymoo.model.problem import Problem
from pymoo.algorithms.nsga3 import NSGA3
from pymoo.algorithms.unsga3 import UNSGA3
import numpy as np
from pymoo.factory import get_reference_directions, get_termination, get_performance_indicator
from pymoo.optimize import minimize
from asgiref.sync import sync_to_async
import plotly.express as pe
import plotly.graph_objects as go
import plotly



class TemplateProblem(Problem):
    def __init__(self, nvar, nobj, ncostr, xl, xu, fs, gs, name=None):
        super().__init__(n_var=nvar, n_obj=nobj, n_constr=ncostr, xl=xl, xu=xu)
        self.fs = fs
        self.gs = gs
        self.name = name

    def _evaluate(self, x, out, *args, **kwargs):
        f_results = []
        for f in self.fs:
          lf = lambda x: eval(f)
          f_results.append(lf(x))
        g_results = []
        for g in self.gs:
          lf = lambda x: eval(g)
          g_results.append(lf(x))
        out["F"] = np.column_stack(f_results)
        out["G"] = np.column_stack(g_results)

def moo_tasks(task_id):
  task = TaskModel.objects.get(id=task_id)
  task.status = StatusEnum.LAUNCHED.value
  task.start_time = django.utils.timezone.now()
  task.save()

  #create duplicate of problem
  dup_problem = task.problem_fk
  dup_problem.pk = None
  dup_problem.isused = True
  dup_problem.save()
  task.problem_fk = dup_problem
  task.save()
  
  for fg in task.fgs_fk.all():
    task.fgs_fk.remove(fg)
    fg.pk = None
    fg.isused = True
    fg.save()
    task.fgs_fk.add( fg )
    task.save()

  task_fs = [ fg.f for fg in task.fgs_fk.all() ]
  task_gs = [ fg.g for fg in task.fgs_fk.all() ]

  problem = TemplateProblem(nvar = task.problem_fk.nvar,
                            nobj = task.problem_fk.nobj,
                            ncostr = task.problem_fk.ncostr,
                            xl = eval(task.problem_fk.xl),
                            xu = eval(task.problem_fk.xu),
                            fs = task_fs,
                            gs = task_gs,
                            name=task.problem_fk.problem_name)

  nsga3_task(task_id=task_id, problem=problem)
  unsga3_task(task_id=task_id, problem=problem)

  if task.status == StatusEnum.LAUNCHED.value:
    task.status = StatusEnum.SUCCES.value
  task.end_time = django.utils.timezone.now()
  task.save()


def nsga3_task(task_id, problem):
  task = TaskModel.objects.get(pk=task_id)
  if task.is_hv:
    hv = get_performance_indicator("hv", ref_point=problem.xu)

  for alg in task.nsga3_fk.all():
    task.nsga3_fk.remove(alg)
    alg.pk = None
    alg.isused = True
    alg.save()
    task.nsga3_fk.add(alg)

    if alg.ref_dirs:
      ref_dirs = eval(alg.ref_dirs)
    else:
      ref_dirs = get_reference_directions(alg.auto_ref_dirs_method, 
                                          alg.auto_ref_dirs_dimensions, 
                                          n_partitions=alg.auto_ref_dirs_npartitions,
                                          scalling=2)
      alg.ref_dirs = ref_dirs.tolist()
      alg.save()

    nsga3 = NSGA3(ref_dirs = ref_dirs)
    nsga3.pop_size = alg.pop_size
    nsga3.eliminate_duplicates = alg.eliminate_duplicates,
    if alg.n_offsprings.isdigit():
      nsga3.n_offsprings = int(alg.n_offsprings)
      
    term = get_termination('n_gen', alg.n_gen)

    res = minimize(problem=problem, algorithm=nsga3, termination=term, save_history=True)
    hstry_x = []
    hstry_f = []
    hstry_g = []
    for h in res.history:
      tmp_list = list(h.opt.get("X"))
      for indx in range(len(tmp_list)):
        tmp_list[indx] = list(tmp_list[indx])
      hstry_x.append(tmp_list)

      tmp_list = list(h.opt.get("F"))
      for indx in range(len(tmp_list)):
        tmp_list[indx] = list(tmp_list[indx])
      hstry_f.append(tmp_list)

      tmp_list = list(h.opt.get("G"))
      for indx in range(len(tmp_list)):
        tmp_list[indx] = list(tmp_list[indx])
      hstry_g.append(tmp_list)
    res_mod = ResultModel(task_fk=task,
                        nsga3_fk=alg,
                        problem_fk=task.problem_fk,
                        result_x=res.X.tolist(),
                        hstry_x=hstry_x,
                        result_f=res.F.tolist(),
                        hstry_f=hstry_f,
                        result_g=res.G.tolist(),
                        hstry_g=hstry_g,
                        hvs=[ [ hv.calc(np.array(f)) for f in F  ] for F in hstry_f] if task.is_hv else None)
    res_mod.save()

    hvs_gens_fig = pe.line(
      x=list(range(1,alg.n_gen+1)),
      y=[ max(hv_lst) for hv_lst in res_mod.hvs],
      title="Best HyperVolume by generation.",
    )
    hvs_gens_fig.update_layout(
      xaxis_title="GEN",
      yaxis_title="BEST HV IN GEN"
    )
    res_mod.hvs_gens_fig = plotly.io.to_html(fig=hvs_gens_fig,full_html=False)
    res_mod.save()

    if len(alg.ref_dirs[0]) == 2:
      ref_dirs_fig = pe.scatter(x=np.array(ref_dirs)[:,0], 
                                y=np.array(ref_dirs)[:,1],
                                labels={"x":"0","y":"1"})
      res_mod.ref_dirs_fig = plotly.io.to_html(fig=ref_dirs_fig, full_html=False)
      res_mod.save()
    elif len(alg.ref_dirs[0]) == 3:
      ref_dirs_fig = pe.scatter_3d(x=np.array(ref_dirs)[:,0], 
                                  y=np.array(ref_dirs)[:,1], 
                                  z=np.array(ref_dirs)[:,2],
                                  labels={"x":"0","y":"1","z":"2"})
      res_mod.ref_dirs_fig = plotly.io.to_html(fig=ref_dirs_fig, full_html=False)
      res_mod.save()
    else:
      values_np = np.array(alg.ref_dirs)
      ref_dirs_fig = go.Figure(data=go.Splom(
        dimensions=[ dict(label=f"{v}",values=values_np[:,v]) for v in range(len(values_np[0])) ],
        diagonal_visible=False
      ))
      res_mod.ref_dirs_fig = plotly.io.to_html(fig=ref_dirs_fig, full_html=False)
      res_mod.save()


def unsga3_task(task_id, problem):
  task = TaskModel.objects.get(id=task_id)
  if task.is_hv:
    hv = get_performance_indicator("hv", ref_point=problem.xu)

  for alg in task.unsga3_fk.all():
    task.unsga3_fk.remove(alg)
    alg.pk = None
    alg.isused = True
    alg.save()
    task.unsga3_fk.add(alg)
    if alg.ref_dirs:
      ref_dirs = eval(alg.ref_dirs)
    else:
      ref_dirs = get_reference_directions(alg.auto_ref_dirs_method, 
                                          alg.auto_ref_dirs_dimensions, 
                                          n_partitions=alg.auto_ref_dirs_npartitions)
      alg.ref_dirs = ref_dirs.tolist()
      alg.save()

    unsga3 = UNSGA3(ref_dirs = ref_dirs)
    unsga3.pop_size = alg.pop_size
    unsga3.eliminate_duplicates = alg.eliminate_duplicates,
    if alg.n_offsprings.isdigit():
      unsga3.n_offsprings = int(alg.n_offsprings)

    term = get_termination('n_gen', alg.n_gen)

    res = minimize(problem=problem, algorithm= unsga3, termination=term, save_history=True)
    hstry_x = []
    hstry_f = []
    hstry_g = []
    for h in res.history:
      tmp_list = list(h.opt.get("X"))
      for indx in range(len(tmp_list)):
        tmp_list[indx] = list(tmp_list[indx])
      hstry_x.append(tmp_list)

      tmp_list = list(h.opt.get("F"))
      for indx in range(len(tmp_list)):
        tmp_list[indx] = list(tmp_list[indx])
      hstry_f.append(tmp_list)

      tmp_list = list(h.opt.get("G"))
      for indx in range(len(tmp_list)):
        tmp_list[indx] = list(tmp_list[indx])
      hstry_g.append(tmp_list)
    res_mod = ResultModel(task_fk=task,
                        unsga3_fk=alg,
                        problem_fk=task.problem_fk,
                        result_x=res.X.tolist(),
                        hstry_x=hstry_x,
                        result_f=res.F.tolist(),
                        hstry_f=hstry_f,
                        result_g=res.G.tolist(),
                        hstry_g=hstry_g,
                        hvs=[ [ hv.calc(np.array(f)) for f in F  ] for F in hstry_f] if task.is_hv else None)
    res_mod.save()


    hvs_gens_fig = pe.line(
      x=list(range(1,alg.n_gen+1)),
      y=[ max(hv_lst) for hv_lst in res_mod.hvs],
      title="Best HyperVolume by generation.",
    )
    hvs_gens_fig.update_layout(
      xaxis_title="GEN",
      yaxis_title="BEST HV IN GEN"
    )
    res_mod.hvs_gens_fig = plotly.io.to_html(fig=hvs_gens_fig,full_html=False)
    res_mod.save()

    if len(alg.ref_dirs[0]) == 2:
      ref_dirs_fig = pe.scatter(x=np.array(ref_dirs)[:,0], 
                                y=np.array(ref_dirs)[:,1],
                                labels={"x":"0","y":"1"})
      res_mod.ref_dirs_fig = plotly.io.to_html(fig=ref_dirs_fig, full_html=False)
      res_mod.save()
    elif len(alg.ref_dirs[0]) == 3:
      ref_dirs_fig = pe.scatter_3d(x=np.array(ref_dirs)[:,0], 
                                  y=np.array(ref_dirs)[:,1], 
                                  z=np.array(ref_dirs)[:,2],
                                  labels={"x":"0","y":"1","z":"2"})
      res_mod.ref_dirs_fig = plotly.io.to_html(fig=ref_dirs_fig, full_html=False)
      res_mod.save()
    else:
      values_np = np.array(alg.ref_dirs)
      ref_dirs_fig = go.Figure(data=go.Splom(
        dimensions=[ dict(label=f"{v}",values=values_np[:,v]) for v in range(len(values_np[0])) ],
        diagonal_visible=False
      ))
      res_mod.ref_dirs_fig = plotly.io.to_html(fig=ref_dirs_fig, full_html=False)
      res_mod.save()