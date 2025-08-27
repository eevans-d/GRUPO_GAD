INSERT INTO gad.usuarios (telegram_id, nombre, nivel) VALUES
(1000000001, 'Admin', '3'), (1000000002, 'Supervisor', '2'), (1000000003, 'Efectivo', '1')
ON CONFLICT DO NOTHING;

INSERT INTO gad.efectivos (dni, nombre, especialidad, usuario_id) VALUES
('DNI001', 'Admin', 'Jefatura', 1), ('DNI002', 'Supervisor', 'Patrullaje', 2), ('DNI003', 'Efectivo', 'Investigación', 3)
ON CONFLICT DO NOTHING;

-- Tareas históricas para heurísticas (10 para P50/P75)
DO $$ BEGIN FOR i IN 1..10 LOOP
  INSERT INTO gad.tareas (codigo, titulo, tipo, inicio_real, fin_real, estado, delegado_usuario_id)
  VALUES ('HIST-' || i, 'Histórica ' || i, 'allanamiento', NOW() - INTERVAL (i*2 || ' hours'), NOW() - INTERVAL (i*2 - 1 || ' hours'), 'finalizada', 1);
END LOOP; END $$;
