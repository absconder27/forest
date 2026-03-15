import { useState } from 'react';
import { motion } from 'motion/react';
import type { JugglingObjectData } from '../data/objects';

interface Props {
  data: JugglingObjectData;
  index: number;
  position: { x: number; y: number };
}

export default function JugglingObject({ data, index, position }: Props) {
  const [imageError, setImageError] = useState(false);
  const [showTooltip, setShowTooltip] = useState(false);

  const floatDuration = 3 + (index % 3) * 0.5;
  const rotateDuration = 4 + (index % 3) * 0.5;
  const delay = index * 0.15;

  const handleClick = () => {
    if (data.link && data.link !== '#') {
      window.open(data.link, '_blank', 'noopener,noreferrer');
    }
  };

  const handleTouchStart = () => {
    setShowTooltip((prev) => !prev);
  };

  return (
    <motion.div
      className="absolute cursor-pointer z-10"
      style={{
        left: `${position.x}%`,
        top: `${position.y}%`,
        transform: 'translate(-50%, -50%)',
      }}
      initial={{ scale: 0, opacity: 0 }}
      animate={{ scale: 1, opacity: 1 }}
      transition={{ delay: 0.3 + delay, duration: 0.4, ease: 'backOut' }}
    >
      <motion.div
        animate={{
          y: [-8, 8, -8],
          rotate: [-5, 5, -5],
        }}
        transition={{
          y: { duration: floatDuration, repeat: Infinity, ease: 'easeInOut' },
          rotate: { duration: rotateDuration, repeat: Infinity, ease: 'easeInOut' },
        }}
        whileHover={{ scale: 1.2, zIndex: 20 }}
        whileTap={{ scale: 1.1 }}
        onClick={handleClick}
        onTouchStart={handleTouchStart}
        onMouseEnter={() => setShowTooltip(true)}
        onMouseLeave={() => setShowTooltip(false)}
        className="relative flex flex-col items-center"
      >
        <div className="w-25 h-25 md:w-32 md:h-32 flex items-center justify-center">
          {!imageError ? (
            <img
              src={data.image}
              alt={data.label}
              className="w-full h-full object-contain drop-shadow-md"
              onError={() => setImageError(true)}
              draggable={false}
            />
          ) : (
            <div className="w-full h-full rounded-full bg-gray-100 border-2 border-gray-300 flex items-center justify-center">
              <span className="text-xs text-gray-500 text-center leading-tight px-1">
                {data.label}
              </span>
            </div>
          )}
        </div>

        {showTooltip && (
          <motion.div
            initial={{ opacity: 0, y: 4 }}
            animate={{ opacity: 1, y: 0 }}
            className="absolute -bottom-8 whitespace-nowrap bg-black/80 text-white text-xs px-2 py-1 rounded pointer-events-none"
          >
            {data.tooltip}
          </motion.div>
        )}
      </motion.div>
    </motion.div>
  );
}
