import { useState } from 'react';

export default function CharacterIllustration() {
  const [imageError, setImageError] = useState(false);
  const hasCustomImage = true;

  if (hasCustomImage && !imageError) {
    return (
      <img
        src="/images/character.png"
        alt="Kyurim Kim"
        className="w-full max-w-xs md:max-w-sm h-auto drop-shadow-sm"
        onError={() => setImageError(true)}
      />
    );
  }

  return (
    <svg
      viewBox="0 0 200 300"
      className="w-full max-w-xs md:max-w-sm h-auto drop-shadow-sm"
      style={{
        stroke: '#000',
        strokeWidth: 4,
        strokeLinecap: 'round',
        strokeLinejoin: 'round',
        fill: 'none',
      }}
    >
      <path d="M 80 85 C 90 75, 120 80, 130 95" strokeWidth="8" />
      <path d="M 75 120 C 65 80, 135 70, 140 120 C 145 170, 85 180, 75 120 Z" />
      <circle cx="100" cy="105" r="2" fill="#000" stroke="none" />
      <circle cx="120" cy="105" r="2" fill="#000" stroke="none" />
      <path d="M 105 120 Q 110 125 115 120" strokeWidth="3" />
      <path d="M 75 145 C 55 155, 60 125, 60 125" />
      <circle cx="55" cy="120" r="5" strokeWidth="4" />
      <path d="M 130 155 C 150 145, 150 120, 150 120" />
      <circle cx="155" cy="115" r="5" strokeWidth="4" />
      <path d="M 80 170 L 75 250" />
      <path d="M 125 170 L 125 240" />
    </svg>
  );
}
