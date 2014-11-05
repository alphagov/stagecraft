/* find module type id */
SELECT id FROM dashboards_moduletype where name like '%bar%';
/* find all dashboards with this module */
SELECT dashboards_dashboard.slug, 
       dashboards_module.slug 
FROM   dashboards_dashboard 
       JOIN dashboards_module 
         ON dashboards_dashboard.id = dashboards_module.dashboard_id 
WHERE  dashboards_module.type_id = '99d99ec4-0f39-4e8a-8168-fc5fc783ca5b' 
LIMIT  10; 
