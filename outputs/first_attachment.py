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
