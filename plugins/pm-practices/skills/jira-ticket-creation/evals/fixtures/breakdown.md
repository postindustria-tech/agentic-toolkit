# User request

Turn this into tickets. Use the project settings below. Treat the brief as the
controlling source; the user is available for questions. No live requests are
permitted in this exercise. Produce the structure plan and, assuming the user
confirms it as proposed, the full drafts and self-check. Do not create anything.
Save your response in the provided output directory.

## Brief

"Add scheduled reports. An admin picks a saved report, a schedule (daily or
weekly, with time and time zone), and recipients (workspace members only).
The system renders the report to PDF at the scheduled time and emails it. Admins
can pause, resume and delete a schedule and see the last run status with an
error message if the run failed. Failed runs retry once after 15 minutes. If the
saved report is deleted, its schedules are deleted too and the admin gets an
in-app notice. No external email addresses in this phase."

## Project settings

Private config supplied for this exercise:
base_url=https://jira.example.invalid; project_key=DEMO;
story_points_field=customfield_99999.
Issue types from the project view: Epic (hierarchy 1), Task and Bug (hierarchy 0),
Subtask (hierarchy -1, subtask). Story is not enabled. Required on create for all
types: Project, Reporter, Summary; Subtask also requires Parent.
No existing ticket matched "scheduled report", "report schedule" or "report
email" in open or recently delivered work (query recorded, one page, complete).
There is an open Epic DEMO-7 "Reporting" (hierarchy 1) that the user named as
the intended parent.
No repository is available.
