import { motion } from 'motion/react';

export default function ContactSection() {
  return (
    <section className="py-20 flex flex-col items-center gap-6">
      <motion.h2
        className="font-handwriting text-3xl text-gray-800"
        initial={{ opacity: 0 }}
        whileInView={{ opacity: 1 }}
        viewport={{ once: true }}
      >
        say hello
      </motion.h2>

      <div className="flex flex-col items-center gap-3 font-handwriting text-xl">
        <a
          href="https://www.instagram.com/kyurimkim/"
          target="_blank"
          rel="noopener noreferrer"
          className="text-gray-600 hover:text-black transition-colors"
        >
          @kyurimkim
        </a>
        <a
          href="mailto:forest@grandeclipfnb.com"
          className="text-gray-600 hover:text-black transition-colors"
        >
          forest@grandeclipfnb.com
        </a>
      </div>
    </section>
  );
}
