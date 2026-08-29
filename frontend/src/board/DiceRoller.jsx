import die1 from '../assets/dice/die-1.svg'
import die2 from '../assets/dice/die-2.svg'
import die3 from '../assets/dice/die-3.svg'
import die4 from '../assets/dice/die-4.svg'
import die5 from '../assets/dice/die-5.svg'
import die6 from '../assets/dice/die-6.svg'

const DIE_FACES = [die1, die2, die3, die4, die5, die6]

function DiceRoller({ lastRoll, turnNumber }) {
  const rollKey = lastRoll ? `${turnNumber}-${lastRoll.join(',')}` : `${turnNumber}-none`

  if (!lastRoll) return null

  return (
    <div key={rollKey} className="dice-roll-anim" style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
      <img src={DIE_FACES[lastRoll[0] - 1]} width={34} height={34} alt={`die ${lastRoll[0]}`} />
      <img src={DIE_FACES[lastRoll[1] - 1]} width={34} height={34} alt={`die ${lastRoll[1]}`} />
      <span style={{ fontSize: 13, color: 'var(--color-muted)', fontWeight: 600 }}>
        rolled {lastRoll[0] + lastRoll[1]}
      </span>
    </div>
  )
}

export default DiceRoller
