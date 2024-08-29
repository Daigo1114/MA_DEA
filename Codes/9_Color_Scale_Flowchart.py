
from matplotlib import pyplot as plt
import numpy as np


def create_colorscale_image():
    # Create a gradient image
    gradient = np.linspace(0, 1, 256)
    gradient = np.vstack((gradient, gradient))
    
    fig, ax = plt.subplots(figsize=(6, 1))
    ax.set_title('Emission Color Scale')
    ax.imshow(gradient, aspect='auto', cmap=plt.get_cmap('RdYlGn_r'))
    ax.set_axis_off()
    
    plt.figtext(0.01, 0.5, 'Low', va='center', ha='left', fontsize=10)
    plt.figtext(0.99, 0.5, 'High', va='center', ha='right', fontsize=10)
    
    plt.subplots_adjust(left=0.05, right=0.95)
    plt.savefig('colorscale.png', dpi=300, bbox_inches='tight')
    plt.close()

# Call this function to create and save the color scale image
create_colorscale_image()