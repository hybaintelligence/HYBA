import React from 'react';

export interface ButtonProps {
  children: React.ReactNode;
  className?: string;
  variant?: 'default' | 'destructive' | 'outline' | 'secondary' | 'ghost' | 'link';
  size?: 'default' | 'sm' | 'lg' | 'icon';
  onClick?: () => void;
  type?: 'button' | 'submit' | 'reset';
}

export const Button: React.FC<ButtonProps> = ({ 
  children, 
  className, 
  variant = 'default',
  size = 'default',
  onClick,
  type = 'button'
}) => (
  <button 
    className={className}
    onClick={onClick}
    type={type}
  >
    {children}
  </button>
);
