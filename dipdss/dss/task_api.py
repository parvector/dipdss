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
    if alg.ref_dirs == "":
      ref_dirs = get_reference_directions(alg.auto_ref_dirs_method, 
                                          alg.auto_ref_dirs_dimensions, 
                                          n_partitions=alg.auto_ref_dirs_npartitions)
    else:
      ref_dirs = np.array(eval(alg.ref_dirs))


    nsga3 = NSGA3(ref_dirs = ref_dirs)
    nsga3.pop_size = alg.pop_size
    nsga3.eliminate_duplicates = alg.eliminate_duplicates,
    if alg.n_offsprings.isdigit():
      nsga3.n_offsprings = int(alg.n_offsprings)
      
    term = get_termination('n_gen', alg.n_gen)

    res = minimize(problem=problem, algorithm= nsga3, termination=term, save_history=True)
    res_mod = ResultModel(task_fk=task,
                        nsga3_fk=alg,
                        problem_fk=task.problem_fk,
                        result_x=res.X,
                        result_f=res.F,
                        result_g=res.G,
                        hv=hv.calc(res.F) if task.is_hv else None,)
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
    if alg.ref_dirs == "":
      ref_dirs = get_reference_directions(alg.auto_ref_dirs_method, 
                                          alg.auto_ref_dirs_dimensions, 
                                          n_partitions=alg.auto_ref_dirs_npartitions)
    else:
      ref_dirs = np.array(eval(alg  .ref_dirs))

    unsga3 = UNSGA3(ref_dirs = ref_dirs)
    unsga3.pop_size = alg.pop_size
    unsga3.eliminate_duplicates = alg.eliminate_duplicates,
    if alg.n_offsprings.isdigit():
      unsga3.n_offsprings = int(alg.n_offsprings)

    term = get_termination('n_gen', alg.n_gen)

    res = minimize(problem=problem, algorithm= unsga3, termination=term, save_history=True)
    res_mod = ResultModel(task_fk=task,
                        unsga3_fk=alg,
                        problem_fk=task.problem_fk,
                        result_x=res.X,
                        result_f=res.F,
                        result_g = res.G,
                        hv= hv.calc(res.F) if task.is_hv else None)
    res_mod.save()