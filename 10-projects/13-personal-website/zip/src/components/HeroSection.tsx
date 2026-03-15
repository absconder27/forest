import CharacterIllustration from './CharacterIllustration';
import JugglingObject from './JugglingObject';
import { objects } from '../data/objects';

function getArchPositions(count: number) {
  const positions: { x: number; y: number }[] = [];
  for (let i = 0; i < count; i++) {
    const angle = Math.PI + (Math.PI * (i + 0.5)) / count;
    const radiusX = 38;
    const radiusY = 25;
    const x = 45 + radiusX * Math.cos(angle);
    const y = 42 + radiusY * Math.sin(angle);
    positions.push({ x, y });
  }
  return positions;
}

export default function HeroSection() {
  const positions = getArchPositions(objects.length);

  return (
    <section className="min-h-screen flex flex-col items-center justify-center relative px-4">
      <div className="relative w-full max-w-lg md:max-w-2xl aspect-square">
        {objects.map((obj, i) => (
          <JugglingObject
            key={obj.id}
            data={obj}
            index={i}
            position={positions[i]}
          />
        ))}

        <div className="absolute inset-0 flex items-end justify-center pb-4 md:pb-8">
          <CharacterIllustration />
        </div>
      </div>

    </section>
  );
}
