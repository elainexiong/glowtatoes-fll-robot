"""Existing robot: original seven Runs in official SPIKE 3 Python.

DEFINITIONS ONLY: no main(), no runloop.run(), no automatic robot motion.
Drive: original pair A/E (left A, right E). Attachments: B and F.
Do not use this port configuration on the new E/A drive robot.
Each Run preserves its old/new PID calls and original parameters.
Only call await run_selected(number) after placing the EXISTING robot at base.
Migration is not field calibration. Blocks/Python speed and timing differ.
"""

# START HERE: read run_1() near the bottom to see a short action sequence.
# A function is like a My Block: it groups instructions under a name.
# Defining a function does not run it. See the README for the startup section.
# Lines starting with # are comments for people; Python ignores them.
# Imports load LEGO tools. port names sockets; motion_sensor reads Hub angles.
from hub import port, motion_sensor
# Control individual motors, such as the two attachment motors.
import motor
# Control the left and right drive motors together.
import motor_pair
# Start async tasks and pause without freezing every other task.
import runloop
# Read the clock so a controller can measure elapsed time.
import time


# SETUP: these names store the original robot's port assignments.
# Left and right are viewed from behind the robot, facing forward.
LEFT_PORT = port.A
RIGHT_PORT = port.E
PAIR = motor_pair.PAIR_1

# Python velocity uses degrees/second; Blocks uses percent. This is a
# starting conversion for LARGE motors, not a measured Blocks equivalence.
# A speed scale in motor degrees/second; not a measured Blocks equivalent.
FULL_SPEED_DPS = 1050
# How quickly drive speed changes; a lower value gives gentler starts.
ACCELERATION = 1000
# Wait about 10 milliseconds between control updates (1000 ms = 1 second).
LOOP_MS = 10

# SPIKE 3 raw yaw is in decidegrees, with the opposite sign to Word Blocks.
# On your mounted Hub, yaw_degrees() must increase when turned RIGHT.
# Yaw means the robot's left/right heading. Our reading should increase RIGHT.
YAW_SIGN = -1
# The direction we want to face. A decimal number can hold part of a degree.
target_heading = 0.0


# Convert the Hub's tenths of a degree into ordinary degrees.
def yaw_degrees():
    return YAW_SIGN * motion_sensor.tilt_angles()[0] / 10.0


# Set up drive motors and a starting direction while the robot is stationary.
def initialize_drive():
    """Call while stationary, once at the start, not between new motions."""
    # global means this function updates the shared target, not a local copy.
    global target_heading
    motor_pair.pair(PAIR, LEFT_PORT, RIGHT_PORT)
    motion_sensor.reset_yaw(0)
    target_heading = 0.0


# A helper keeps a number between -maximum and +maximum.
# Example: _limit(70, 50) returns 50. An initial _ marks an internal helper.
def _limit(value, maximum):
    return max(-maximum, min(maximum, value))


# Send one drive command. This starts motion; it does not wait for a distance.
# steering 0 means straight; 100 requests turning in place, NOT 100 degrees.
# round() rounds a number; int() converts it to a whole number for the API.
def _move(speed_percent, steering):
    motor_pair.move(
        PAIR,
        int(round(_limit(steering, 100))),
        velocity=int(round(_limit(speed_percent, 100) * FULL_SPEED_DPS / 100.0)),
        acceleration=ACCELERATION,
    )


# PID decides how strongly to correct an error: desired value minus reading.
# P reacts to today's error; I remembers past errors; D follows error changes.
# kp, ki, kd control the strength of these three parts; zero disables a part.
# dt is time since the previous update. Smoothing softens sudden D changes.
def _pid_step(error, last_error, integral, derivative, dt, kp, ki, kd, smoothing):
    # Preserve the source's per-iteration sum (not error * dt).
    # += means add to the saved value. This copy sums error each loop, not error × dt.
    integral += error
    # Avoid dividing by a tiny time interval; otherwise measure error change/second.
    raw_d = 0.0 if dt < 0.001 else (error - last_error) / dt
    derivative = smoothing * derivative + (1.0 - smoothing) * raw_d
    # Multiply each part by its gain, then add the three corrections.
    output = kp * error + ki * integral + kd * derivative
    # return sends values back to the function that called us.
    return output, integral, derivative


# NEW STRAIGHT: first input is RIGHT MOTOR degrees, not cm or robot turn angle.
# Positive requests forward; negative requests reverse. timeout is in seconds.
# async lets this function pause at await; callers await it to wait for the move.
# Here PID adjusts travel speed; a separate yaw correction steers the robot.
async def moveforward_pid_new(targetdegree, kp, ki, kd, timeout):
    """Signed RIGHT motor degrees; seconds timeout. Positive = forward.

    Preserves the source's absolute-position stop condition, even if a
    wheel turns the wrong way. Verify direction before floor tests.
    """
    if timeout <= 0:
        raise ValueError("timeout must be positive seconds")
    # Start the distance counter at zero. This does not physically move a wheel.
    motor.reset_relative_position(LEFT_PORT, 0)
    motor.reset_relative_position(RIGHT_PORT, 0)
    start = time.ticks_ms()
    last_time = 0.0
    integral = 0.0
    last_error = targetdegree
    derivative = 0.0

    try:
        while True:
            position = motor.relative_position(RIGHT_PORT)
            # abs() ignores the sign. This checks distance magnitude, not travel direction.
            reached = abs(position) > abs(targetdegree) - 2
            elapsed = time.ticks_diff(time.ticks_ms(), start) / 1000.0
            # or means either condition can end the move: target reached OR time used up.
            if reached or elapsed > timeout:
                reason = "target" if reached else "timeout"
                # break leaves this control loop.
                break

            # How many motor degrees remain? The sign helps choose forward or reverse.
            error = targetdegree - position
            output, integral, derivative = _pid_step(
                error, last_error, integral, derivative,
                elapsed - last_time, kp, ki, kd, 0.4,
            )
            # Cap speed, then use lower caps as the remaining distance gets smaller.
            output = _limit(output, 50)
            if abs(error) < 150:
                output = _limit(output, 25)
            if abs(error) < 50:
                output = _limit(output, 12)

            # Compare actual direction with desired direction; reverse needs opposite steering.
            heading_error = yaw_degrees() - target_heading
            steering = heading_error if output < 0 else -heading_error
            _move(output, steering)
            last_time = elapsed
            last_error = error
            # Pause briefly so the next reading is later and other tasks can run too.
            await runloop.sleep_ms(LOOP_MS)
    # Always do this cleanup when the try block exits, including on an error.
    finally:
        motor_pair.stop(PAIR, stop=motor.BRAKE)

    # Return a dictionary of named results; tests can print it in the console.
    return {
        "reason": reason,
        "elapsed_s": time.ticks_diff(time.ticks_ms(), start) / 1000.0,
        "right_degrees": motor.relative_position(RIGHT_PORT),
        "yaw_degrees": yaw_degrees(),
    }


# NEW TURN: first input is ROBOT degrees. Positive = right; negative = left.
# Unlike the old turn below, this adds to the remembered target heading.
async def turning_right_pid_new(targetdegree, kp, ki, kd, timeout):
    """Relative body angle: positive right, negative left; timeout seconds.

    Adds to target_heading; neither this nor straight driving resets yaw.
    As in the source, there is no angle-wrap handling or settling interval.
    """
    # global means this function updates the shared target, not a local copy.
    global target_heading
    if timeout <= 0:
        raise ValueError("timeout must be positive seconds")
    # Example: desired heading 30 plus a right 45 turn gives a new target of 75.
    target_heading += targetdegree
    last_error = target_heading - yaw_degrees()
    last_time = 0.0
    integral = 0.0
    derivative = 0.0
    start = time.ticks_ms()

    try:
        while True:
            error = target_heading - yaw_degrees()
            # Close enough to stop: heading error is less than one degree right now.
            reached = abs(error) < 1
            elapsed = time.ticks_diff(time.ticks_ms(), start) / 1000.0
            # or means either condition can end the move: target reached OR time used up.
            if reached or elapsed > timeout:
                reason = "target" if reached else "timeout"
                # break leaves this control loop.
                break

            output, integral, derivative = _pid_step(
                error, last_error, integral, derivative,
                elapsed - last_time, kp, ki, kd, 0.5,
            )
            # Limit turn speed; slow further within 30 degrees and again within 10.
            output = _limit(output, 25)
            if abs(error) < 30:
                output = _limit(output, 10)
            if abs(error) < 10:
                output = _limit(output, 5)

            _move(output, 100)
            last_time = elapsed
            last_error = error
            # Pause briefly so the next reading is later and other tasks can run too.
            await runloop.sleep_ms(LOOP_MS)
    # Always do this cleanup when the try block exits, including on an error.
    finally:
        motor_pair.stop(PAIR, stop=motor.BRAKE)

    # Return a dictionary of named results; tests can print it in the console.
    return {
        "reason": reason,
        "elapsed_s": time.ticks_diff(time.ticks_ms(), start) / 1000.0,
        "target_heading": target_heading,
        "yaw_degrees": yaw_degrees(),
    }


# Original Blocks motor speeds persist between Runs; initial default assumed 50%.
# Verify medium-motor speed mapping on the original attachments before using Runs.
# A dictionary links a text name, such as "B", to its actual Hub port.
ATTACHMENT_PORTS = {"B": port.B, "F": port.F}
ATTACHMENT_FULL_SPEED_DPS = 1110
# Remember each attachment's speed percentage. These start at 50% on restart.
_attachment_speeds = {"B": 50, "F": 50}


# Pair the original drive motors before a selected Run begins.
def _setup_run():
    motor_pair.pair(PAIR, LEFT_PORT, RIGHT_PORT)


# Reset both the sensor reading and our remembered direction to zero.
def _reset_heading():
    # global means this function updates the shared target, not a local copy.
    global target_heading
    motion_sensor.reset_yaw(0)
    target_heading = 0.0


# Convert seconds to milliseconds, then wait. _wait(0.5) pauses half a second.
async def _wait(seconds):
    await runloop.sleep_ms(int(round(seconds * 1000)))


# Save a speed for later attachment moves; this line alone moves nothing.
def _set_attachment_speed(name, percent):
    _attachment_speeds[name] = percent


# Move one attachment, then wait for it to finish.
# rotations counts motor turns: 0.5 rotation = 180 motor degrees.
# Motor direction does not automatically tell us whether an attachment rises.
async def _attachment_turn(name, direction, rotations):
    # Clockwise viewed at the motor output = positive motor velocity.
    sign = 1 if direction == "clockwise" else -1
    velocity = int(round(_attachment_speeds[name] * ATTACHMENT_FULL_SPEED_DPS / 100))
    try:
        await motor.run_for_degrees(
            ATTACHMENT_PORTS[name], int(round(abs(rotations) * 360)),
            sign * velocity, stop=motor.BRAKE,
        )
    # Always do this cleanup when the try block exits, including on an error.
    finally:
        motor.stop(ATTACHMENT_PORTS[name], stop=motor.BRAKE)


# OLD STRAIGHT: uses motor degrees too, but controls for the WHOLE duration.
# It can move back and forth near the target; it does not finish early there.
async def moveforward_pid(targetdegree, kp, ki, kd, timeout):
    """OLD distance PID: resets yaw, runs until timeout, can reverse near target.

    Intentionally distinct from PID New. Original target_heading is NOT updated
    by this yaw reset; retained for source fidelity, including mixed-call risk.
    """
    if timeout <= 0:
        raise ValueError("timeout must be positive seconds")
    # Start the distance counter at zero. This does not physically move a wheel.
    motor.reset_relative_position(LEFT_PORT, 0)
    motor.reset_relative_position(RIGHT_PORT, 0)
    motion_sensor.reset_yaw(0)
    start = time.ticks_ms()
    last_time = integral = derivative = last_error = 0.0
    try:
        # Keep controlling until time is up, even if the target was reached earlier.
        while last_time <= timeout:
            elapsed = time.ticks_diff(time.ticks_ms(), start) / 1000.0
            error = targetdegree - motor.relative_position(RIGHT_PORT)
            output, integral, derivative = _pid_step(
                error, last_error, integral, derivative,
                elapsed - last_time, kp, ki, kd, 0.4,
            )
            yaw = yaw_degrees()
            _move(output, yaw if output < 0 else -yaw)
            last_time, last_error = elapsed, error
            # Pause briefly so the next reading is later and other tasks can run too.
            await runloop.sleep_ms(LOOP_MS)
    # Always do this cleanup when the try block exits, including on an error.
    finally:
        motor_pair.stop(PAIR, stop=motor.BRAKE)
    return {"reason": "duration", "right_degrees": motor.relative_position(RIGHT_PORT),
            "yaw_degrees": yaw_degrees()}


# OLD TURN: starts its yaw reading at zero each time and runs for the duration.
# Its target is relative to that fresh zero, not the New controller's target.
async def turning_right_pid(targetdegree, kp, ki, kd, timeout):
    """OLD turn PID: resets yaw each call and controls for full timeout.

    targetdegree is relative to the reset yaw, not an accumulated heading.
    """
    if timeout <= 0:
        raise ValueError("timeout must be positive seconds")
    motion_sensor.reset_yaw(0)
    start = time.ticks_ms()
    last_time = integral = derivative = last_error = 0.0
    try:
        # Keep controlling until time is up, even if the target was reached earlier.
        while last_time <= timeout:
            elapsed = time.ticks_diff(time.ticks_ms(), start) / 1000.0
            error = targetdegree - yaw_degrees()
            output, integral, derivative = _pid_step(
                error, last_error, integral, derivative,
                elapsed - last_time, kp, ki, kd, 0.5,
            )
            _move(output, 100)
            last_time, last_error = elapsed, error
            # Pause briefly so the next reading is later and other tasks can run too.
            await runloop.sleep_ms(LOOP_MS)
    # Always do this cleanup when the try block exits, including on an error.
    finally:
        motor_pair.stop(PAIR, stop=motor.BRAKE)
    return {"reason": "duration", "yaw_degrees": yaw_degrees()}


# Stop the drive pair, then each attachment motor. BRAKE resists rotation.
def _stop_all():
    motor_pair.stop(PAIR, stop=motor.BRAKE)
    for attachment_port in ATTACHMENT_PORTS.values():
        motor.stop(attachment_port, stop=motor.BRAKE)


# =================================================================
# RUN 1: follow the commands below from top to bottom.
# Each await waits for its action before the next action starts.
# Movement calls: target, P gain, I gain, D gain, seconds.
# Straight targets are MOTOR degrees; turn targets are ROBOT degrees.
async def run_1():
    """Original Run 1; action order and parameters retained."""
    # Use the original A/E drive pair.
    _setup_run()
    # Use the starting direction as zero for this Run.
    _reset_heading()
    # Step 1: request forward travel of 835 motor degrees (New PID).
    await moveforward_pid_new(835, 0.25, 0, 0.2, 4)
    # Step 2: request a 60-degree left turn (old PID).
    await turning_right_pid(-60, 0.7, 0, 0.3, 1.5)
    # Step 3: request a 60-degree right turn (old PID).
    await turning_right_pid(60, 1.3, 0, 0.3, 1.5)
    # Step 4: request reverse travel of 850 motor degrees (old PID).
    await moveforward_pid(-850, 1.3, 0, 0.4, 2)


# =================================================================
# RUN 2: follow the commands below from top to bottom.
# Each await waits for its action before the next action starts.
# Movement calls: target, P gain, I gain, D gain, seconds.
# Straight targets are MOTOR degrees; turn targets are ROBOT degrees.
async def run_2():
    """Original Run 2; action order and parameters retained."""
    # Use the original A/E drive pair.
    _setup_run()
    # Use the starting direction as zero for this Run.
    _reset_heading()
    # Step 1: request forward travel of 590 motor degrees (New PID).
    await moveforward_pid_new(590, 1.1, 0, 0.3, 4)
    # Step 2: request reverse travel of 495 motor degrees (New PID).
    await moveforward_pid_new(-495, 1.3, 0, 0.4, 4)
    # Step 3: request a 50-degree right turn (New PID).
    await turning_right_pid_new(50, 1.3, 0, 0.4, 4)
    # Step 4: request forward travel of 605 motor degrees (New PID).
    await moveforward_pid_new(605, 1.3, 0, 0.4, 4)
    # Step 5: turn attachment F counterclockwise for 0.5 motor rotations.
    await _attachment_turn('F', 'counterclockwise', 0.5)
    # Step 6: request reverse travel of 600 motor degrees (old PID).
    await moveforward_pid(-600, 1.3, 0, 0.4, 2)


# =================================================================
# RUN 3: follow the commands below from top to bottom.
# Each await waits for its action before the next action starts.
# Movement calls: target, P gain, I gain, D gain, seconds.
# Straight targets are MOTOR degrees; turn targets are ROBOT degrees.
async def run_3():
    """Original Run 3; action order and parameters retained."""
    # Use the original A/E drive pair.
    _setup_run()
    # Use the starting direction as zero for this Run.
    _reset_heading()
    # Step 1: turn attachment F counterclockwise for 0.4 motor rotations.
    await _attachment_turn('F', 'counterclockwise', 0.4)
    # Step 2: request forward travel of 800 motor degrees (New PID).
    await moveforward_pid_new(800, 1.3, 0, 0.5, 4)
    # Step 3: request a 90-degree right turn (New PID).
    await turning_right_pid_new(90, 1.3, 0, 0.4, 4)
    # Step 4: request forward travel of 410 motor degrees (New PID).
    await moveforward_pid_new(410, 1.3, 0, 0.4, 4)
    # Step 5: request a 90-degree left turn (New PID).
    await turning_right_pid_new(-90, 1.3, 0, 0.4, 4)
    # Pause for 0.5 seconds before continuing.
    await _wait(0.5)
    # Step 6: request forward travel of 130 motor degrees (old PID).
    await moveforward_pid(130, 1.3, 0, 0.4, 2)
    # Set attachment F speed to 100% for its following moves.
    _set_attachment_speed('F', 100)
    # Step 7: turn attachment F clockwise for 0.3 motor rotations.
    await _attachment_turn('F', 'clockwise', 0.3)
    # Step 8: turn attachment F counterclockwise for 0.3 motor rotations.
    await _attachment_turn('F', 'counterclockwise', 0.3)
    # Pause for 0.5 seconds before continuing.
    await _wait(0.5)
    # Step 9: request forward travel of 132 motor degrees (old PID).
    await moveforward_pid(132, 1.4, 0, 0.4, 2)
    # Repeat the two indented turns twice. _ is an unused loop counter.
    for _ in range(2):
        # Step 10: request a 5-degree right turn (old PID).
        await turning_right_pid(5, 3, 0, 0.4, 0.5)
        # Step 11: request a 5-degree left turn (old PID).
        await turning_right_pid(-5, 3, 0, 0.4, 0.5)
    # Pause for 0.5 seconds before continuing.
    await _wait(0.5)
    # Step 12: request reverse travel of 180 motor degrees (old PID).
    await moveforward_pid(-180, 1.3, 0, 0.4, 2)
    # Step 13: request a 130-degree left turn (old PID).
    await turning_right_pid(-130, 1.3, 0, 0.4, 1.5)
    # Step 14: request forward travel of 770 motor degrees (old PID).
    await moveforward_pid(770, 1.3, 0, 0.4, 3)


# =================================================================
# RUN 4: follow the commands below from top to bottom.
# Each await waits for its action before the next action starts.
# Movement calls: target, P gain, I gain, D gain, seconds.
# Straight targets are MOTOR degrees; turn targets are ROBOT degrees.
async def run_4():
    """Original Run 4; action order and parameters retained."""
    # Use the original A/E drive pair.
    _setup_run()
    # Use the starting direction as zero for this Run.
    _reset_heading()
    # Step 1: request forward travel of 1010 motor degrees (New PID).
    await moveforward_pid_new(1010, 1, 0, 0.5, 4)
    # Step 2: request a 5-degree right turn (New PID).
    await turning_right_pid_new(5, 1, 0, 0.5, 4)
    # Set attachment F speed to 100% for its following moves.
    _set_attachment_speed('F', 100)
    # Step 3: turn attachment F clockwise for 0.4 motor rotations.
    await _attachment_turn('F', 'clockwise', 0.4)
    # Step 4: request a 5-degree left turn (New PID).
    await turning_right_pid_new(-5, 1.3, 0, 0.4, 4)
    # Step 5: request reverse travel of 595 motor degrees (New PID).
    await moveforward_pid_new(-595, 1.3, 0, 0.4, 4)
    # Step 6: request a 90-degree right turn (New PID).
    await turning_right_pid_new(90, 1.3, 0, 0.4, 4)
    # Step 7: request forward travel of 1790 motor degrees (New PID).
    await moveforward_pid_new(1790, 1.3, 0, 0.4, 6)
    # Step 8: request a 90-degree left turn (New PID).
    await turning_right_pid_new(-90, 1.3, 0, 0.4, 4)
    # Step 9: turn attachment B counterclockwise for 0.08 motor rotations.
    await _attachment_turn('B', 'counterclockwise', 0.08)
    # Step 10: request forward travel of 645 motor degrees (New PID).
    await moveforward_pid_new(645, 1.3, 0, 0.4, 4)
    # Step 11: turn attachment B clockwise for 0.2 motor rotations.
    await _attachment_turn('B', 'clockwise', 0.2)
    # Step 12: request reverse travel of 115 motor degrees (New PID).
    await moveforward_pid_new(-115, 1.3, 0, 0.4, 4)
    # Step 13: request forward travel of 30 motor degrees (New PID).
    await moveforward_pid_new(30, 1.3, 0, 0.4, 4)
    # Step 14: turn attachment B counterclockwise for 0.5 motor rotations.
    await _attachment_turn('B', 'counterclockwise', 0.5)
    # Step 15: request a 90-degree left turn (New PID).
    await turning_right_pid_new(-90, 1.3, 0, 0.4, 4)
    # Step 16: request forward travel of 412 motor degrees (New PID).
    await moveforward_pid_new(412, 1.3, 0, 0.4, 4)
    # Step 17: request a 135-degree right turn (New PID).
    await turning_right_pid_new(135, 1.3, 0, 0.4, 4)
    # Step 18: request forward travel of 165 motor degrees (New PID).
    await moveforward_pid_new(165, 0.6, 0, 0.4, 4)
    # Step 19: request reverse travel of 80 motor degrees (New PID).
    await moveforward_pid_new(-80, 1.3, 0, 0.4, 4)
    # Step 20: request a 90-degree left turn (New PID).
    await turning_right_pid_new(-90, 1.3, 0, 0.4, 4)
    # Step 21: request reverse travel of 1000 motor degrees (old PID).
    await moveforward_pid(-1000, 1.3, 0, 0.4, 3)


# =================================================================
# RUN 5: follow the commands below from top to bottom.
# Each await waits for its action before the next action starts.
# Movement calls: target, P gain, I gain, D gain, seconds.
# Straight targets are MOTOR degrees; turn targets are ROBOT degrees.
async def run_5():
    """Original Run 5; action order and parameters retained."""
    # Use the original A/E drive pair.
    _setup_run()
    # Step 1: request forward travel of 900 motor degrees (old PID).
    await moveforward_pid(900, 1.3, 0, 0.5, 2.5)
    # Step 2: request a 45-degree right turn (old PID).
    await turning_right_pid(45, 1.3, 0, 0.4, 1.5)
    # Step 3: request forward travel of 200 motor degrees (old PID).
    await moveforward_pid(200, 1.3, 0, 0.4, 1.5)
    # Set attachment B speed to 50% for its following moves.
    _set_attachment_speed('B', 50)
    # Step 4: turn attachment B clockwise for 0.6 motor rotations.
    await _attachment_turn('B', 'clockwise', 0.6)
    # Step 5: turn attachment B counterclockwise for 0.6 motor rotations.
    await _attachment_turn('B', 'counterclockwise', 0.6)
    # Step 6: request reverse travel of 120 motor degrees (old PID).
    await moveforward_pid(-120, 1.3, 0, 0.4, 1.5)
    # Step 7: request a 30-degree right turn (old PID).
    await turning_right_pid(30, 1.3, 0, 0.4, 2)
    # Step 8: request forward travel of 48 motor degrees (old PID).
    await moveforward_pid(48, 1.3, 0, 0.4, 1.5)
    # Set attachment F speed to 25% for its following moves.
    _set_attachment_speed('F', 25)
    # Step 9: turn attachment F clockwise for 0.26 motor rotations.
    await _attachment_turn('F', 'clockwise', 0.26)
    # Step 10: request reverse travel of 200 motor degrees (old PID).
    await moveforward_pid(-200, 1.3, 0, 0.4, 1.5)
    # Step 11: request a 85-degree right turn (old PID).
    await turning_right_pid(85, 1.3, 0, 0.4, 1)
    # Step 12: request forward travel of 780 motor degrees (old PID).
    await moveforward_pid(780, 1.3, 0, 0.4, 2)


# =================================================================
# RUN 6: follow the commands below from top to bottom.
# Each await waits for its action before the next action starts.
# Movement calls: target, P gain, I gain, D gain, seconds.
# Straight targets are MOTOR degrees; turn targets are ROBOT degrees.
async def run_6():
    """Original Run 6; action order and parameters retained."""
    # Use the original A/E drive pair.
    _setup_run()
    # Step 1: request forward travel of 390 motor degrees (old PID).
    await moveforward_pid(390, 1.3, 0, 0.5, 2)
    # Step 2: turn attachment F counterclockwise for 0.3 motor rotations.
    await _attachment_turn('F', 'counterclockwise', 0.3)
    # Pause for 1 seconds before continuing.
    await _wait(1)
    # Step 3: turn attachment B clockwise for 0.1 motor rotations.
    await _attachment_turn('B', 'clockwise', 0.1)
    # Step 4: request reverse travel of 100 motor degrees (old PID).
    await moveforward_pid(-100, 2, 0, 0.4, 1.5)
    # Step 5: request forward travel of 50 motor degrees (old PID).
    await moveforward_pid(50, 1.3, 0, 0.4, 1.5)
    # Step 6: turn attachment F clockwise for 0.5 motor rotations.
    await _attachment_turn('F', 'clockwise', 0.5)
    # Step 7: request reverse travel of 400 motor degrees (old PID).
    await moveforward_pid(-400, 1.3, 0, 0.4, 2)


# =================================================================
# RUN 7: follow the commands below from top to bottom.
# Each await waits for its action before the next action starts.
# Movement calls: target, P gain, I gain, D gain, seconds.
# Straight targets are MOTOR degrees; turn targets are ROBOT degrees.
async def run_7():
    """Original Run 7; action order and parameters retained."""
    # Use the original A/E drive pair.
    _setup_run()
    # Use the starting direction as zero for this Run.
    _reset_heading()
    # Step 1: request forward travel of 416 motor degrees (New PID).
    await moveforward_pid_new(416, 1.3, 0, 0.5, 4)
    # Pause for 0.5 seconds before continuing.
    await _wait(0.5)
    # Set attachment F speed to 30% for its following moves.
    _set_attachment_speed('F', 30)
    # Step 2: turn attachment F clockwise for 0.15 motor rotations.
    await _attachment_turn('F', 'clockwise', 0.15)
    # Step 3: request reverse travel of 212 motor degrees (New PID).
    await moveforward_pid_new(-212, 1, 0, 0.5, 4)
    # Step 4: request a 6-degree right turn (New PID).
    await turning_right_pid_new(6, 1, 0, 0.4, 2)
    # Set attachment F speed to 5% for its following moves.
    _set_attachment_speed('F', 5)
    # Step 5: turn attachment F counterclockwise for 0.1 motor rotations.
    await _attachment_turn('F', 'counterclockwise', 0.1)
    # Step 6: request reverse travel of 150 motor degrees (old PID).
    await moveforward_pid(-150, 1.3, 0, 0.4, 1.5)


# CHOOSE ONE RUN: a dictionary maps each number to its function.
# The functions are stored without () here: we choose first, then call one.
# This is not a Hub-button menu, and it never automatically chains seven Runs.
async def run_selected(number):
    """Run exactly ONE selected mission sequence; never chain all seven."""
    runs = {1: run_1, 2: run_2, 3: run_3, 4: run_4,
            5: run_5, 6: run_6, 7: run_7}
    if number not in runs:
        # Reject a number that is not in the choices instead of starting a wrong Run.
        raise ValueError("Select Run 1 through 7")
    try:
        # [] selects the function; () calls it; await waits for its sequence to finish.
        await runs[number]()
    # Always do this cleanup when the try block exits, including on an error.
    finally:
        _stop_all()

# No startup call is included. This project will NOT move the robot by itself.
# Later, an explicit entry point can select one Run, for example:
# async def main():
#     await run_selected(1)
# runloop.run(main())
