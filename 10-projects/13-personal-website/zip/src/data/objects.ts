export interface JugglingObjectData {
  id: string;
  label: string;
  image: string;
  link: string;
  tooltip: string;
}

export const objects: JugglingObjectData[] = [
  {
    id: 'newmix',
    label: 'Newmix Coffee',
    image: '/images/newmix-stick.png',
    link: 'https://www.instagram.com/newmix.coffee/',
    tooltip: 'Brand Director @ Newmix',
  },
  {
    id: 'journal',
    label: 'Journal',
    image: '/images/journal.png',
    link: 'https://www.instagram.com/kyurimkim/',
    tooltip: 'Writing & Reflection',
  },
  {
    id: 'headphones',
    label: 'Nothing Ear',
    image: '/images/headphones.png',
    link: '#',
    tooltip: 'Music & Podcasts',
  },
  {
    id: 'book1',
    label: 'Book 1',
    image: '/images/book1.jpg',
    link: '#',
    tooltip: 'Reading List',
  },
  {
    id: 'book2',
    label: 'Book 2',
    image: '/images/book2.jpg',
    link: '#',
    tooltip: 'Favorite Reads',
  },
];
