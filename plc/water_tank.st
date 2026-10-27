PROGRAM water_tank
  VAR
    main_level  : INT := 100;
    tank1_level : INT := 0;
    tank2_level : INT := 0;
    tank3_level : INT := 0;
    valve1      : BOOL := FALSE;
    valve2      : BOOL := FALSE;
    valve3      : BOOL := FALSE;
  END_VAR

  IF tank1_level < 80 AND main_level > 0 THEN
    valve1 := TRUE;
  ELSE
    valve1 := FALSE;
  END_IF;

  IF tank2_level < 80 AND main_level > 0 THEN
    valve2 := TRUE;
  ELSE
    valve2 := FALSE;
  END_IF;

  IF tank3_level < 80 AND main_level > 0 THEN
    valve3 := TRUE;
  ELSE
    valve3 := FALSE;
  END_IF;

  IF valve1 = TRUE THEN
    tank1_level := tank1_level + 1;
    main_level  := main_level - 1;
  END_IF;

  IF valve2 = TRUE THEN
    tank2_level := tank2_level + 1;
    main_level  := main_level - 1;
  END_IF;

  IF valve3 = TRUE THEN
    tank3_level := tank3_level + 1;
    main_level  := main_level - 1;
  END_IF;

  IF main_level < 0 THEN main_level := 0; END_IF;
  IF tank1_level > 100 THEN tank1_level := 100; END_IF;
  IF tank2_level > 100 THEN tank2_level := 100; END_IF;
  IF tank3_level > 100 THEN tank3_level := 100; END_IF;

END_PROGRAM

CONFIGURATION Config0
  RESOURCE Res0 ON PLC
    TASK TaskMain(INTERVAL := T#500ms, PRIORITY := 0);
    PROGRAM Inst0 WITH TaskMain : water_tank;
  END_RESOURCE
END_CONFIGURATION
