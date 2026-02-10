// Craco configuration to use external PostCSS config (needed for Tailwind v4)
module.exports = {
    style: {
        postcss: {
            mode: 'file',
        },
    },
};
