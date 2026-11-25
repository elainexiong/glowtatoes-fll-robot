# First moves: original robot, left drive A and right drive E.
from hub import port
import motor
import motor_pair
import runloop

PAIR = motor_pair.PAIR_1
SPEED = 200  # Motor degrees per second.

async def move_for(steering, speed, milliseconds):
    try:
        motor_pair.move(PAIR, steering, velocity=speed)
        await runloop.sleep_ms(milliseconds)
    finally:
        motor_pair.stop(PAIR, stop=motor.BRAKE)
    await runloop.sleep_ms(500)

async def main():
    motor_pair.pair(PAIR, port.A, port.E)
    await runloop.sleep_ms(1000)

    print("Forward")
    await move_for(0, SPEED, 1000)

    print("Backward")
    await move_for(0, -SPEED, 1000)

    print("Turn right")
    await move_for(100, SPEED, 500)

    print("Turn left")
    await move_for(-100, SPEED, 500)

    print("Finished!")

runloop.run(main())
