# GLOWTATOES — From Word Blocks to Python

Start with a few familiar moves, then load and test the team's seven-Run Python program. This guide uses **official SPIKE 3 Python** and the **original robot**.

**Your path:** open SPIKE → connect → try First Moves → download the mission code → calibrate → test Run 1.

Keep your original Blocks project. First Moves and the seven-Run migration will be separate Python projects.

[Robot repository](https://github.com/elainexiong/glowtatoes-fll-robot) · [Team website repository](https://github.com/elainexiong/growtatoes)

## 1. Open the SPIKE App

**Already installed?** Open it and choose **SPIKE Prime**. Keep your Blocks project and create a new **Python** project called **First Moves**. Delete its starter code; you will paste the demo in Section 4. No reinstall is needed if the Python editor supports `motor`, `motor_pair`, and `runloop`; check **Knowledge Base → API Modules**. If it only offers the older `from spike import PrimeHub` API, update the app.

**Not installed?** [Download the official SPIKE App](https://education.lego.com/en-us/downloads/spike-app/software/), install it, choose **SPIKE Prime**, and create a new **Python** project called **First Moves**. Delete its starter code.

Use official SPIKE Python for this project. You do not need Pybricks, desktop Python, or extra packages.

## 2. Check the ports

Identify left and right while standing behind the robot, facing forward.

| Port | Motor |
| --- | --- |
| **A** | Left drive |
| **E** | Right drive |
| **B** | Attachment B |
| **F** | Attachment F |

These are the original V2 assignments. The separate new-chassis test project uses reversed drive ports—do not copy its setup here.

## 3. Connect the Hub

1. Turn on the charged Hub and connect it with a data-capable USB cable.
2. Click **Connect** in SPIKE. Complete any required Hub OS update without disconnecting it.
3. Confirm motors appear on **A, E, B, and F**.

For wireless testing, press the Hub's Bluetooth button and select the Hub through SPIKE's **Connect** screen. Confirm Bluetooth is connected before unplugging USB.

## 4. First moves: try Python

Before calibration, try a tiny program that makes the robot **move forward, move backward, turn right, and turn left**. It uses basic motor commands, not PID or any of the seven Runs.

1. In the **First Moves** project you created in Section 1, paste the complete program below. **No mission-code download is needed yet.**
2. Confirm the original robot is connected: **left A, right E**. Leave clear space around it; attachment motors will stay still.
3. Press **Play**. It waits one second, performs four short moves with pauses, then stops. Use **Stop** if a direction looks wrong.

```python
# This is a complete program for a separate "First Moves" Python project.
# It uses the original robot's drive motors: left A, right E.
from hub import port  # Port names such as port.A and port.E.
import motor         # Motor constants, including the BRAKE stop mode.
import motor_pair    # Commands that control two drive motors together.
import runloop       # Starts async functions and provides timed waits.

# A variable gives a value a name. These names are reused below.
PAIR = motor_pair.PAIR_1  # The software label for our drive-motor pair.
SPEED = 200               # Motor shaft speed in degrees per second, not percent.

# "def" defines a function; it does not run it yet.
# "async" allows the function to pause at an "await".
# Parameters are inputs supplied each time we call this function.
async def move_for(steering, speed, milliseconds):
    try:
        # Start both wheels. This command starts motion without waiting.
        # steering: 0 = straight; +100 / -100 = opposite turns in place.
        # speed: positive = forward; negative = backward.
        motor_pair.move(PAIR, steering, velocity=speed)
        # Keep this function waiting while the motors continue moving.
        # 1000 milliseconds (ms) equals 1 second.
        await runloop.sleep_ms(milliseconds)
    finally:
        # "finally" runs when this block finishes, including on an error.
        # BRAKE resists wheel rotation; it does not reverse the motors.
        motor_pair.stop(PAIR, stop=motor.BRAKE)
    # Pause for half a second after each move so you can see each step.
    await runloop.sleep_ms(500)

# main() contains the sequence we want the robot to follow.
# Indented lines belong to the function or block directly above them.
async def main():
    # Register the left motor FIRST and the right motor SECOND.
    motor_pair.pair(PAIR, port.A, port.E)
    # Give yourself one second before the first movement starts.
    await runloop.sleep_ms(1000)

    # print() sends a message to the SPIKE console.
    # await waits for move_for() to finish before starting the next step.
    print("Forward")
    await move_for(0, SPEED, 1000)   # Straight forward for 1 second.

    print("Backward")
    await move_for(0, -SPEED, 1000)  # Minus sign reverses the speed.

    print("Turn right")
    await move_for(100, SPEED, 500)  # Turn for 0.5 seconds, NOT 100 degrees.

    print("Turn left")
    await move_for(-100, SPEED, 500) # Turn the other way for 0.5 seconds.

    print("Finished!")

# The definitions above do nothing until this line starts main().
# Keep exactly ONE active runloop.run(...) startup call in the project.
runloop.run(main())
```

### What the Python means

| Code | Meaning |
| --- | --- |
| `import` | Load the tools the program needs. |
| `SPEED = 200` | Give a value a name so it is easy to change. |
| `async def move_for(...)` | Define a reusable movement function. |
| `await` | Wait for this step before continuing to the next one. |
| Indented lines | Belong to the function or block above them. |
| `runloop.run(main())` | Start the program. |

In `move_for(steering, speed, milliseconds)`, steering **0** means straight; **100 / -100** request opposite turns in place. Those values are **not turn angles**. A negative speed requests backward movement. **1000 milliseconds = 1 second.**

Try changing the forward duration from `1000` to `1500`, or `SPEED` from `200` to `250`—one change at a time. The robot should move longer or faster. Keep enough clear space for the change.

This is a timed movement demo: it does not promise an exact distance, a 90-degree turn, or a return to the exact starting point. Once all four directions work, save **First Moves**. You are ready to download the team's mission program in Section 5.

### Optional: move an attachment motor

Now try **one motor by itself**. The drive wheels stay still: attachment motor **B** turns 90°, pauses, then turns 90° back.

Create another Python project called **First Attachment**, delete its starter code, and paste the complete program below. **Do not append it to First Moves or the seven-Run code.** Use an unloaded motor, or first confirm the attached mechanism can move this far without hitting a stop.

```python
# Optional First Moves exercise: only attachment motor B moves.
# Use an unloaded motor, or confirm the mechanism allows this travel.
from hub import port
import motor
import runloop

ATTACHMENT = port.B  # Change to port.F to test the other attachment motor.
SPEED = 200          # Motor degrees per second, not a percentage.

async def main():
    await runloop.sleep_ms(1000)  # Wait one second before starting.
    try:
        # Inputs: port, motor degrees to travel, signed speed.
        # await waits for this movement to finish before the next line.
        await motor.run_for_degrees(ATTACHMENT, 90, SPEED)
        await runloop.sleep_ms(500)
        # A negative speed turns the same motor in the opposite direction.
        await motor.run_for_degrees(ATTACHMENT, 90, -SPEED)
        print("Attachment exercise finished!")
    finally:
        motor.stop(ATTACHMENT, stop=motor.BRAKE)

runloop.run(main())
```

Here, **90 means motor-shaft degrees**, not the robot's turning angle or necessarily the attachment's angle. `SPEED` sets how fast it moves; the minus sign reverses direction. Change `port.B` to `port.F` to try the other motor, one at a time.

The two `await` calls run **one after the other**. This exercise does not run the attachment and drive wheels together. Returning the motor by the same angle also does not automatically home the attachment.


## 5. Download the code

Download the files from the team repository:

1. Open the [team robot repository](https://github.com/elainexiong/glowtatoes-fll-robot), choose **Code → Download ZIP**, and unzip it.
2. Open the `outputs` folder.
3. Keep an untouched copy before making changes.

| Mission file in `outputs` | Use |
| --- | --- |
| [`Existing Robot - Seven Runs Python.llsp3`](outputs/Existing%20Robot%20-%20Seven%20Runs%20Python.llsp3) | Open directly in SPIKE. |
| [`existing_robot_seven_runs.py`](outputs/existing_robot_seven_runs.py) | Copy into a new Python project. |

The mission program was converted from **`v2_glowtatoes.llsp3`**, keeping the original ports, action order, parameters, and old/New PID calls. It has passed action checks; complete Runs still need original-robot testing.

## 6. Open a separate seven-Run project

Keep **First Moves** saved as its own project. For the seven-Run program, choose either option:

- **Open the project:** use SPIKE's open/import option and select `Existing Robot - Seven Runs Python.llsp3`.
- **Paste the source:** create a **Python** project, delete its starter code, and paste the entire contents of `existing_robot_seven_runs.py`.

Name this working project **Seven Runs — Calibration**. It is separate from **First Moves** and your Blocks project. When loading a new version, replace the old contents—do not append another copy.

The mission files contain functions but **no active startup call**, so pressing Play now will not start a Run. Section 7 adds calibration tests; Section 8 adds the mission launcher. **Do not copy the First Moves program into this project.**

## 7. Before Run 1: check and calibrate

Python can run the same commands at different speeds or with different stopping behavior. **Measure first; change one setting at a time.** Keep the original values so you can undo changes.

### A. Check direction and yaw

In **Seven Runs — Calibration**, append this temporary test after the complete migrated code. These examples use helpers defined in that file; they will not work in First Moves by itself. Keep **only one active startup section** at a time.

```python
# Paste this AFTER the full seven-Run code, not into First Moves alone.
# The migration already defines initialize_drive(), the PID, and _stop_all().
async def main():
    initialize_drive()  # Set up A/E drive motors and the heading reference.
    await runloop.sleep_ms(1000)  # Wait 1 second; keep the robot still.
    motion_sensor.reset_yaw(0)   # Treat this starting direction as zero.
    try:
        # Inputs, in order: motor degrees, P gain, I gain, D gain, timeout.
        # 180 is a short forward move; it is NOT 180 cm or a robot turn.
        # P = 0.25; I and D are zero for this first isolated check.
        # The final 3 allows up to 3 seconds for this New PID move.
        result = await moveforward_pid_new(180, 0.25, 0, 0, 3)
        # result is a dictionary: named values such as "reason" and
        # "right_degrees". Read it in the console after the move.
        print(result)
    finally:
        # Stop drive and attachment motors when this block ends.
        _stop_all()

# Start this test once. Remove other active startup calls first.
runloop.run(main())
```

Press **Play** with space ahead and the Stop control ready. For the first direction check, support the drive wheels off the floor.

- Both wheels should drive forward. `right_degrees` should be positive and close to 180.
- Change `180` to `-180` for a separate reverse check, with space behind the robot.
- For a yaw-only check, replace the `result = ...` and `print(result)` lines with:

```python
        # Replace the movement and print lines INSIDE the existing try block.
        # This loop reads yaw only; it does not command any motor movement.
        # range(100) repeats the indented body 100 times.
        # "_" means we do not need to use the loop counter.
        for _ in range(100):
            print(yaw_degrees())  # Show the robot's current heading in degrees.
            await runloop.sleep_ms(100)  # Wait 0.1 seconds between readings.
```

Keep the robot still while it zeros, then turn it gently by hand. **Right should increase yaw; left should decrease it.** If reversed, verify the setup before changing `YAW_SIGN` (currently `-1`). Zero yaw only after physically aligning the robot; zeroing does not straighten it.

### B. Measure straight travel

In the first test, replace the movement call with:

```python
        # Replace only the movement line inside the calibration test.
        # 600 motor degrees requests a longer forward move; measure its travel.
        # Keep P = 0.25, I = 0, D = 0; allow up to 8 seconds.
        result = await moveforward_pid_new(600, 0.25, 0, 0, 8)
```

Measure the distance and sideways drift. Repeat three times from the same marked start, then test reverse separately.

**600 means motor degrees, not centimeters.** Record how far this robot actually travels; do not reuse the new chassis's measurements.

If travel is consistently too short or long **and the target was reached**, a trial correction is:

```text
# Use only for a repeatable distance error after the encoder target is reached.
# This is a formula to calculate yourself, not Python to paste into SPIKE.
new distance target = old target × desired distance / measured distance
```

Change only the relevant move's first argument and retest. If the result says `timeout`, diagnose that first. Random sideways drift is not a distance-scale error.

### C. Check turns and PID response

Replace the straight-movement call with a single-turn test:

```python
        # Replace only the movement line inside the calibration test.
        # Here the first input is ROBOT turn degrees, not motor degrees.
        # +45 requests a right turn; use -45 for a separate left-turn trial.
        # P = 0.5, I = 0, D = 0; allow up to 6 seconds.
        result = await turning_right_pid_new(45, 0.5, 0, 0, 6)
```

Measure the physical angle after stopping. Test positive and negative angles separately: 30°, 45°, 60°, and 90°. Reset the robot's position before each trial.

For isolated checks, start with P only (`ki = kd = 0`). Then test the actual gains from Run 1. The original gains may need retuning because Python's loop timing differs from Blocks.

- Repeated overshoot or hunting: try less P; evaluate D after P is stable.
- Add I only if a repeatable remaining error requires it.
- Straight-move PID gains control **distance**, while yaw steering is a separate P correction. Changing distance `ki`/`kd` does not tune heading correction.
- Keep `LOOP_MS = 10` while tuning. There is no separate heading-gain setting in this version; changing heading response requires editing the helper.

### D. Know what to adjust

These are starting values in the migration, not a request to replace them all:

| If you observe… | Check or adjust… |
| --- | --- |
| Wrong drive direction | Ports A/E and motor direction first. |
| Wrong yaw sign | Verify yaw, then `YAW_SIGN = -1` if needed. |
| Python drives faster/slower than Blocks | `FULL_SPEED_DPS = 1050`; compare the same move before changing distance. |
| Jerky starts | `ACCELERATION = 1000`; try a lower value and retest. |
| Consistently wrong travel distance | The move's motor-degree target, after ruling out timeout. |
| Turn overshoot or repeated corrections | That turn's `kp`, `ki`, `kd`; measure again after braking. |
| Attachment too fast/slow | `ATTACHMENT_FULL_SPEED_DPS = 1110` and the step's `_set_attachment_speed(...)`. |
| Attachment endpoint wrong | Starting position, direction, then the step's rotation amount. |

PID New limits speed as it approaches a target, so increasing P does not always make it faster. Compare elapsed time and stopping behavior with Blocks, not just the final position.

### E. Check attachments and stopping rules

Test B and F separately over a small allowed range. Confirm which direction does the intended action, then measure the rotations needed. Put each attachment in its required starting position yourself: **the code does not automatically home it**.

Attachment speeds start at an assumed **50%** after a fresh program start. Later commands change them. Run 2 uses F without setting its speed first, so confirm that starting assumption before testing it.

Understand these differences before changing timeouts or yaw resets:

| Controller | When it stops |
| --- | --- |
| **PID New** | Target condition or timeout. Check that the printed reason is `target`. |
| **Old PID** | Runs for the supplied duration, even if it reaches the target earlier. |

Increasing an old PID's duration can increase hunting. A New timeout does **not** automatically abort the full mission: the migrated Runs currently continue to the next step. Stop a failed calibration test and diagnose it before proceeding.

Old PID resets yaw; New turns use accumulated `target_heading`. Preserve the existing reset order. This version also lacks continuous yaw-wrap handling; a turn sequence crossing the sensor's angle boundary needs a code review before use.

### F. Ready for Run 1?

Check Run 1's four moves individually with their original parameters:

| Move | Original parameters: target, P, I, D, seconds |
| --- | --- |
| New forward | `835, 0.25, 0, 0.2, 4` |
| Old left turn | `-60, 0.7, 0, 0.3, 1.5` |
| Old right turn | `60, 1.3, 0, 0.3, 1.5` |
| Old reverse | `-850, 1.3, 0, 0.4, 2` |

Run 1 has no attachment-motor commands. Keep a short record of **inputs → measured result → change**. Once forward/reverse directions, distances, turns, and stopping behavior are repeatable, continue below.

## 8. Test and debug one Run

Stay in **Seven Runs — Calibration**. Remove the entire temporary startup section and replace it with:

```python
# Paste this AFTER the full migrated code and remove the calibration launcher.
# Change this one number to choose a mission. Valid choices: 1 through 7.
SELECTED_RUN = 1

async def main():
    # The migration defines run_selected(). It selects ONE Run and
    # attempts to stop all configured motors afterward.
    # await waits for the selected sequence to finish; it does not launch
    # the other six Runs or create a Hub-button selection menu.
    await run_selected(SELECTED_RUN)

# Start the chosen Run when the program launches. Motion can begin immediately.
# Keep exactly ONE active startup call in the project.
runloop.run(main())
```

1. Set the Run number and prepare its attachment.
2. Align the robot at that Run's base starting position.
3. Save, connect, and press **Play**. Movement can start immediately.
4. Watch where the first error appears. Stop and test that step separately; change one parameter and repeat.
5. Return to base and reset the attachment before another attempt.

Only the selected Run executes. **The seven Runs are not chained together.**

There must be exactly **one active `runloop.run(...)` call**. The supplied commented example does not execute.

### Selecting a Run on the Hub

This version does **not** yet include a Hub-button Run-selection menu. Change `SELECTED_RUN` in SPIKE to choose a Run.

A Hub program slot selects a stored program, not automatically a Run inside that program. Transfer the updated project to the intended slot after changing the selection. Confirm that standalone launching works before disconnecting the computer; use the Hub's stop control when disconnected.

## 9. Quick code reference

| Function | Purpose |
| --- | --- |
| `moveforward_pid_new(...)` | Encoder distance control plus yaw steering. |
| `turning_right_pid_new(...)` | Relative turn using accumulated target heading. |
| `moveforward_pid(...)` / `turning_right_pid(...)` | Original older controllers; run for a duration and reset yaw. |
| `_attachment_turn(...)` | Move B or F by motor rotations and direction. |
| `run_selected(number)` | Run one sequence and stop the configured motors afterward. |

**Units:** drive distance = motor degrees; turns = robot degrees; attachment travel = motor rotations; waits/timeouts = seconds.

The original old/New choices remain in place. Calibration changes should be saved in your working copy.

## 10. What is verified?

The original V2 graph matches the migration source. All seven action sequences passed checks for order, parameters, attachment commands, waits, and resets. Ports remain unchanged.

Those checks do not prove physical accuracy. The full seven Runs still need original-robot testing. A correct yaw reading does not prove the robot returned to the same position—measure the offset too.

## 11. Quick fixes

| Problem | Try this |
| --- | --- |
| Play does nothing | Confirm connection and add one active startup section. |
| An old test runs first | Remove duplicate startup calls or old `main()` definitions. |
| `No module named motor` | Run inside SPIKE, not desktop Python. |
| `No module named spike` | Remove legacy API code; use the supplied SPIKE 3 source. |
| Robot moves the wrong way | Recheck left A/right E and Section 7's direction tests. |
| Attachment moves the wrong way | Check B/F and the mechanism's required direction. |
| Hub runs old code | Transfer the updated project to the correct slot. |
| Bluetooth disconnects | Reconnect through SPIKE or use a data-capable USB cable. |

## 12. Development checks

The seven action sequences were compared with the original Blocks graph during development. Those checks used simulated hardware and did not move the robot. The development-only checking tools are not included in this download.

For API help, open **Knowledge Base → Getting Started / API Modules** in SPIKE, or see [LEGO's motor lesson](https://education.lego.com/en-us/lessons/get-moving-with-motors/making-moves-with-motors/).
